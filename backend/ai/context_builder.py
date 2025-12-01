"""
Context Builder - Retrieves and structures database data for AI context.

This module queries the database and builds JSON context objects
that are passed to the LLM for grounded responses.
"""
import re
from typing import Dict, Any, List, Optional, Set
from backend.etl.supabase_client import supabase


class ContextBuilder:
    """Builds structured context from database for AI responses."""

    def __init__(self):
        """Initialize context builder with database client."""
        self.db = supabase

    # =========================================================================
    # Entity Extraction (from user questions)
    # =========================================================================

    def extract_entities_from_question(self, question: str) -> Dict[str, List[str]]:
        """
        Extract potential entity references from a user question.

        Returns dict with keys: drug_names, target_symbols, indication_names
        """
        question_upper = question.upper()

        # Get all known entities from DB for matching
        drugs = self.db.table('epi_drugs').select('name').execute().data
        drug_names = {d['name'].upper(): d['name'] for d in drugs}

        targets = self.db.table('epi_targets').select('symbol').execute().data
        target_symbols = {t['symbol'].upper(): t['symbol'] for t in targets}

        indications = self.db.table('epi_indications').select('name').execute().data
        indication_names = {i['name'].upper(): i['name'] for i in indications}

        # Find matches
        found = {
            "drug_names": [],
            "target_symbols": [],
            "indication_names": []
        }

        for upper_name, original in drug_names.items():
            if upper_name in question_upper:
                found["drug_names"].append(original)

        for upper_sym, original in target_symbols.items():
            # Match whole words only for short symbols
            if len(upper_sym) <= 4:
                if re.search(rf'\b{re.escape(upper_sym)}\b', question_upper):
                    found["target_symbols"].append(original)
            else:
                if upper_sym in question_upper:
                    found["target_symbols"].append(original)

        for upper_name, original in indication_names.items():
            if upper_name in question_upper:
                found["indication_names"].append(original)

        # Also check for target families
        families = ['HDAC', 'BET', 'DNMT', 'EZH2', 'IDH', 'SIRT', 'NSD2', 'KDM']
        for family in families:
            if family in question_upper:
                # Add all targets from this family
                family_targets = self.db.table('epi_targets').select('symbol').ilike('family', f'%{family}%').execute().data
                for t in family_targets:
                    if t['symbol'] not in found["target_symbols"]:
                        found["target_symbols"].append(t['symbol'])

        return found

    # =========================================================================
    # Drug Context
    # =========================================================================

    def get_drug_context(self, drug_name: str) -> Optional[Dict[str, Any]]:
        """Get full context for a drug by name."""
        # Get drug record
        result = self.db.table('epi_drugs').select('*').ilike('name', drug_name).execute()
        if not result.data:
            return None

        drug = result.data[0]
        drug_id = drug['id']

        # Get targets
        targets_result = self.db.table('epi_drug_targets').select(
            'mechanism_of_action, is_primary_target, epi_targets(id, symbol, full_name, family, class)'
        ).eq('drug_id', drug_id).execute()

        targets = []
        for dt in targets_result.data:
            if dt.get('epi_targets'):
                target_info = dt['epi_targets']
                target_info['mechanism'] = dt.get('mechanism_of_action')
                target_info['is_primary'] = dt.get('is_primary_target', False)
                targets.append(target_info)

        # Get indications and scores
        indications_result = self.db.table('epi_drug_indications').select(
            'approval_status, max_phase, epi_indications(id, name, efo_id, disease_area)'
        ).eq('drug_id', drug_id).execute()

        indications = []
        for di in indications_result.data:
            if di.get('epi_indications'):
                ind_info = di['epi_indications']
                ind_info['approval_status'] = di.get('approval_status')
                ind_info['max_phase'] = di.get('max_phase')

                # Get score for this drug-indication pair
                score_result = self.db.table('epi_scores').select('*').eq(
                    'drug_id', drug_id
                ).eq('indication_id', ind_info['id']).execute()

                if score_result.data:
                    ind_info['scores'] = score_result.data[0]

                indications.append(ind_info)

        # Get ChEMBL metrics
        chembl_result = self.db.table('chembl_metrics').select('*').eq('drug_id', drug_id).execute()
        chembl_metrics = chembl_result.data[0] if chembl_result.data else None

        return {
            "drug": drug,
            "targets": targets,
            "indications": indications,
            "chembl_metrics": chembl_metrics
        }

    def get_drugs_by_target(self, target_symbol: str) -> List[Dict[str, Any]]:
        """Get all drugs targeting a specific target."""
        # Get target
        target_result = self.db.table('epi_targets').select('id, symbol, full_name, family, class').eq(
            'symbol', target_symbol
        ).execute()

        if not target_result.data:
            return []

        target = target_result.data[0]

        # Get drugs via drug_targets
        drug_targets = self.db.table('epi_drug_targets').select(
            'drug_id, mechanism_of_action, epi_drugs(id, name, drug_type, fda_approved, modality)'
        ).eq('target_id', target['id']).execute()

        drugs = []
        for dt in drug_targets.data:
            if dt.get('epi_drugs'):
                drug_info = dt['epi_drugs']
                drug_info['mechanism'] = dt.get('mechanism_of_action')
                drugs.append(drug_info)

        return drugs

    # =========================================================================
    # Target Context
    # =========================================================================

    def get_target_context(self, target_symbol: str) -> Optional[Dict[str, Any]]:
        """Get full context for a target by symbol."""
        result = self.db.table('epi_targets').select('*').eq('symbol', target_symbol).execute()
        if not result.data:
            return None

        target = result.data[0]
        target_id = target['id']

        # Get drugs targeting this
        drugs = self.get_drugs_by_target(target_symbol)

        # Get editing assets targeting this
        try:
            editing_result = self.db.table('epi_editing_assets').select('*').eq(
                'target_gene_id', target_id
            ).execute()
            editing_assets = editing_result.data
        except Exception:
            editing_assets = []

        # Get related patents
        try:
            patents_result = self.db.table('epi_patents').select('*').execute()
            related_patents = []
            for p in patents_result.data:
                symbols = p.get('related_target_symbols') or []
                if target_symbol in symbols:
                    related_patents.append(p)
        except Exception:
            related_patents = []

        return {
            "target": target,
            "drugs": drugs,
            "editing_assets": editing_assets,
            "patents": related_patents
        }

    # =========================================================================
    # Indication Context
    # =========================================================================

    def get_indication_context(self, indication_name: str) -> Optional[Dict[str, Any]]:
        """Get full context for an indication by name."""
        result = self.db.table('epi_indications').select('*').ilike('name', f'%{indication_name}%').execute()
        if not result.data:
            return None

        indication = result.data[0]
        indication_id = indication['id']

        # Get drugs for this indication
        drug_indications = self.db.table('epi_drug_indications').select(
            'drug_id, approval_status, max_phase, epi_drugs(id, name, drug_type, fda_approved, modality)'
        ).eq('indication_id', indication_id).execute()

        drugs = []
        for di in drug_indications.data:
            if di.get('epi_drugs'):
                drug_info = di['epi_drugs']
                drug_info['approval_status'] = di.get('approval_status')
                drug_info['max_phase'] = di.get('max_phase')

                # Get score
                score = self.db.table('epi_scores').select('*').eq(
                    'drug_id', drug_info['id']
                ).eq('indication_id', indication_id).execute()
                if score.data:
                    drug_info['scores'] = score.data[0]

                drugs.append(drug_info)

        # Get editing assets for this indication
        editing_result = self.db.table('epi_editing_assets').select('*').eq(
            'indication_id', indication_id
        ).execute()

        return {
            "indication": indication,
            "drugs": drugs,
            "editing_assets": editing_result.data
        }

    # =========================================================================
    # Scorecard Context
    # =========================================================================

    def get_scorecard_context(self, drug_id: str, indication_id: str) -> Optional[Dict[str, Any]]:
        """Get full context for explaining a drug-indication scorecard."""
        # Get drug
        drug_result = self.db.table('epi_drugs').select('*').eq('id', drug_id).execute()
        if not drug_result.data:
            return None
        drug = drug_result.data[0]

        # Get indication
        indication_result = self.db.table('epi_indications').select('*').eq('id', indication_id).execute()
        if not indication_result.data:
            return None
        indication = indication_result.data[0]

        # Get scores
        scores_result = self.db.table('epi_scores').select('*').eq('drug_id', drug_id).eq(
            'indication_id', indication_id
        ).execute()
        scores = scores_result.data[0] if scores_result.data else None

        # Get targets
        targets_result = self.db.table('epi_drug_targets').select(
            'mechanism_of_action, is_primary_target, epi_targets(symbol, full_name, family, class, io_exhaustion_axis, epi_resistance_role)'
        ).eq('drug_id', drug_id).execute()

        targets = []
        for dt in targets_result.data:
            if dt.get('epi_targets'):
                target_info = dt['epi_targets']
                target_info['mechanism'] = dt.get('mechanism_of_action')
                targets.append(target_info)

        # Get ChEMBL metrics
        chembl_result = self.db.table('chembl_metrics').select('*').eq('drug_id', drug_id).execute()
        chembl = chembl_result.data[0] if chembl_result.data else None

        # Get drug-indication link details
        di_result = self.db.table('epi_drug_indications').select('*').eq('drug_id', drug_id).eq(
            'indication_id', indication_id
        ).execute()
        drug_indication = di_result.data[0] if di_result.data else None

        return {
            "drug": drug,
            "indication": indication,
            "scores": scores,
            "targets": targets,
            "chembl_metrics": chembl,
            "drug_indication": drug_indication,
            "scoring_formula": {
                "description": "TotalScore = (0.5 × BioScore) + (0.3 × ChemScore) + (0.2 × TractabilityScore)",
                "bio_weight": 0.5,
                "chem_weight": 0.3,
                "tract_weight": 0.2
            }
        }

    # =========================================================================
    # Editing Asset Context
    # =========================================================================

    def get_editing_asset_context(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Get full context for an epigenetic editing asset."""
        result = self.db.table('epi_editing_assets').select('*').eq('id', asset_id).execute()
        if not result.data:
            return None

        asset = result.data[0]

        # Get target info
        target = None
        if asset.get('target_gene_id'):
            target_result = self.db.table('epi_targets').select('*').eq(
                'id', asset['target_gene_id']
            ).execute()
            if target_result.data:
                target = target_result.data[0]

        # Get indication info
        indication = None
        if asset.get('indication_id'):
            ind_result = self.db.table('epi_indications').select('*').eq(
                'id', asset['indication_id']
            ).execute()
            if ind_result.data:
                indication = ind_result.data[0]

        # Get editing scores
        scores_result = self.db.table('epi_editing_scores').select('*').eq(
            'editing_asset_id', asset_id
        ).execute()
        scores = scores_result.data[0] if scores_result.data else None

        # Get competing small molecule drugs for same target
        competing_drugs = []
        if target:
            competing_drugs = self.get_drugs_by_target(target['symbol'])

        # Get related patents
        related_patents = []
        if asset.get('target_gene_symbol'):
            patents_result = self.db.table('epi_patents').select('*').execute()
            for p in patents_result.data:
                symbols = p.get('related_target_symbols') or []
                if asset['target_gene_symbol'] in symbols:
                    related_patents.append(p)

        return {
            "editing_asset": asset,
            "target": target,
            "indication": indication,
            "scores": scores,
            "competing_drugs": competing_drugs,
            "patents": related_patents,
            "scoring_formula": {
                "description": "TotalEditingScore = (0.5 × TargetBioScore) + (0.3 × ModalityScore) + (0.2 × DurabilityScore)",
                "bio_weight": 0.5,
                "modality_weight": 0.3,
                "durability_weight": 0.2
            }
        }

    # =========================================================================
    # Full Chat Context
    # =========================================================================

    def build_chat_context(
        self,
        question: str,
        entity_refs: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Build comprehensive context for a chat question.

        Args:
            question: The user's question
            entity_refs: Optional pre-extracted entity references

        Returns:
            JSON-serializable context dict
        """
        # Extract entities if not provided
        if not entity_refs:
            entity_refs = self.extract_entities_from_question(question)

        context = {
            "drugs": [],
            "targets": [],
            "indications": [],
            "editing_assets": [],
            "patents": []
        }

        # Fetch drug contexts
        for drug_name in entity_refs.get("drug_names", []):
            drug_ctx = self.get_drug_context(drug_name)
            if drug_ctx:
                context["drugs"].append(drug_ctx)

        # Fetch target contexts
        for target_symbol in entity_refs.get("target_symbols", []):
            target_ctx = self.get_target_context(target_symbol)
            if target_ctx:
                context["targets"].append(target_ctx)

        # Fetch indication contexts
        for ind_name in entity_refs.get("indication_names", []):
            ind_ctx = self.get_indication_context(ind_name)
            if ind_ctx:
                context["indications"].append(ind_ctx)

        # If no specific entities found, provide general stats
        if not any([context["drugs"], context["targets"], context["indications"]]):
            context["database_stats"] = self._get_database_stats()

        return context

    def _get_database_stats(self) -> Dict[str, Any]:
        """Get general database statistics for context."""
        drugs = self.db.table('epi_drugs').select('id, fda_approved').execute().data
        targets = self.db.table('epi_targets').select('id, family').execute().data
        indications = self.db.table('epi_indications').select('id').execute().data
        editing = self.db.table('epi_editing_assets').select('id').execute().data

        # Count by target family
        families = {}
        for t in targets:
            fam = t.get('family', 'other')
            families[fam] = families.get(fam, 0) + 1

        return {
            "total_drugs": len(drugs),
            "approved_drugs": sum(1 for d in drugs if d.get('fda_approved')),
            "pipeline_drugs": sum(1 for d in drugs if not d.get('fda_approved')),
            "total_targets": len(targets),
            "targets_by_family": families,
            "total_indications": len(indications),
            "total_editing_assets": len(editing)
        }
