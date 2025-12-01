#!/usr/bin/env python3
"""
Database Integrity Audit Script
================================
Comprehensive data quality check for pilldreams database.
NO MODIFICATIONS - inspection only.

Run from project root:
    python -m backend.etl.audit_database
"""

import os
from datetime import datetime
from collections import Counter
from typing import Dict, List, Any, Optional
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.etl.supabase_client import supabase


class DatabaseAuditor:
    """Audit database integrity without making changes."""

    def __init__(self):
        self.sb = supabase
        self.findings: List[Dict[str, Any]] = []
        self.stats: Dict[str, Any] = {}

    def log_finding(self, severity: str, table: str, category: str, message: str, details: Optional[Dict] = None):
        """Record an audit finding."""
        finding = {
            "severity": severity,  # CRITICAL, WARNING, INFO
            "table": table,
            "category": category,
            "message": message,
            "details": details or {}
        }
        self.findings.append(finding)

    def audit_epi_targets(self):
        """Audit epi_targets table."""
        print("\n🔍 Auditing epi_targets...")

        # Fetch all targets
        response = self.sb.table('epi_targets').select('*').execute()
        targets = response.data
        self.stats['epi_targets_count'] = len(targets)

        # Check for duplicates by symbol
        symbols = [t['symbol'] for t in targets if t.get('symbol')]
        symbol_counts = Counter(symbols)
        duplicates = {sym: count for sym, count in symbol_counts.items() if count > 1}
        if duplicates:
            self.log_finding(
                "CRITICAL", "epi_targets", "Duplicates",
                f"Found {len(duplicates)} duplicate target symbols",
                {"duplicates": duplicates}
            )

        # Check for missing required fields
        missing_symbol = [t['id'] for t in targets if not t.get('symbol')]
        if missing_symbol:
            self.log_finding(
                "CRITICAL", "epi_targets", "Missing Data",
                f"{len(missing_symbol)} targets missing 'symbol'",
                {"target_ids": missing_symbol}
            )

        missing_name = [t['symbol'] for t in targets if not t.get('name')]
        if missing_name:
            self.log_finding(
                "WARNING", "epi_targets", "Missing Data",
                f"{len(missing_name)} targets missing 'name'",
                {"symbols": missing_name}
            )

        missing_family = [t['symbol'] for t in targets if not t.get('family')]
        if missing_family:
            self.log_finding(
                "WARNING", "epi_targets", "Missing Data",
                f"{len(missing_family)} targets missing 'family'",
                {"symbols": missing_family}
            )

        missing_ensembl = [t['symbol'] for t in targets if not t.get('ensembl_id')]
        if missing_ensembl:
            self.log_finding(
                "WARNING", "epi_targets", "Missing Data",
                f"{len(missing_ensembl)} targets missing 'ensembl_id'",
                {"symbols": missing_ensembl}
            )

        missing_uniprot = [t['symbol'] for t in targets if not t.get('uniprot_id')]
        if missing_uniprot:
            self.log_finding(
                "WARNING", "epi_targets", "Missing Data",
                f"{len(missing_uniprot)} targets missing 'uniprot_id'",
                {"symbols": missing_uniprot}
            )

        # Check annotation fields
        io_annotated = sum(1 for t in targets if t.get('io_exhaustion_axis') is not None)
        self.stats['targets_io_annotated'] = io_annotated
        self.log_finding(
            "INFO", "epi_targets", "Annotation Coverage",
            f"{io_annotated}/{len(targets)} targets have IO exhaustion annotations",
            {"coverage_pct": round(io_annotated / len(targets) * 100, 1)}
        )

        resistance_annotated = sum(1 for t in targets if t.get('epi_resistance_role'))
        self.stats['targets_resistance_annotated'] = resistance_annotated
        self.log_finding(
            "INFO", "epi_targets", "Annotation Coverage",
            f"{resistance_annotated}/{len(targets)} targets have resistance role annotations",
            {"coverage_pct": round(resistance_annotated / len(targets) * 100, 1)}
        )

        print(f"  ✓ Checked {len(targets)} targets")

    def audit_epi_drugs(self):
        """Audit epi_drugs table."""
        print("\n🔍 Auditing epi_drugs...")

        response = self.sb.table('epi_drugs').select('*').execute()
        drugs = response.data
        self.stats['epi_drugs_count'] = len(drugs)

        # Check for duplicates by name
        names = [d['name'] for d in drugs if d.get('name')]
        name_counts = Counter(names)
        duplicates = {name: count for name, count in name_counts.items() if count > 1}
        if duplicates:
            self.log_finding(
                "CRITICAL", "epi_drugs", "Duplicates",
                f"Found {len(duplicates)} duplicate drug names",
                {"duplicates": duplicates}
            )

        # Check for missing ChEMBL IDs
        missing_chembl = [d['name'] for d in drugs if not d.get('chembl_id')]
        if missing_chembl:
            self.log_finding(
                "WARNING", "epi_drugs", "Missing Data",
                f"{len(missing_chembl)} drugs missing 'chembl_id'",
                {"drug_names": missing_chembl}
            )

        # Check for invalid FDA approval dates (future dates)
        today = datetime.now().date()
        future_approvals = []
        for d in drugs:
            if d.get('fda_approval_date'):
                try:
                    approval_date = datetime.fromisoformat(d['fda_approval_date'].replace('Z', '+00:00')).date()
                    if approval_date > today:
                        future_approvals.append({
                            "name": d['name'],
                            "date": d['fda_approval_date']
                        })
                except:
                    pass

        if future_approvals:
            self.log_finding(
                "WARNING", "epi_drugs", "Invalid Data",
                f"{len(future_approvals)} drugs have future FDA approval dates",
                {"drugs": future_approvals}
            )

        # Check source distribution
        sources = Counter([d.get('source', 'unknown') for d in drugs])
        self.stats['drug_sources'] = dict(sources)
        self.log_finding(
            "INFO", "epi_drugs", "Data Distribution",
            f"Drug sources: {dict(sources)}"
        )

        print(f"  ✓ Checked {len(drugs)} drugs")

    def audit_epi_drug_targets(self):
        """Audit epi_drug_targets table."""
        print("\n🔍 Auditing epi_drug_targets...")

        response = self.sb.table('epi_drug_targets').select('*').execute()
        links = response.data
        self.stats['epi_drug_targets_count'] = len(links)

        # Check for orphaned drug references
        drug_response = self.sb.table('epi_drugs').select('id').execute()
        valid_drug_ids = {d['id'] for d in drug_response.data}

        orphaned_drugs = [l['id'] for l in links if l.get('drug_id') not in valid_drug_ids]
        if orphaned_drugs:
            self.log_finding(
                "CRITICAL", "epi_drug_targets", "Orphaned Records",
                f"{len(orphaned_drugs)} drug-target links reference non-existent drugs",
                {"link_ids": orphaned_drugs}
            )

        # Check for orphaned target references
        target_response = self.sb.table('epi_targets').select('id').execute()
        valid_target_ids = {t['id'] for t in target_response.data}

        orphaned_targets = [l['id'] for l in links if l.get('target_id') not in valid_target_ids]
        if orphaned_targets:
            self.log_finding(
                "CRITICAL", "epi_drug_targets", "Orphaned Records",
                f"{len(orphaned_targets)} drug-target links reference non-existent targets",
                {"link_ids": orphaned_targets}
            )

        # Check for missing mechanism of action
        missing_moa = [l['id'] for l in links if not l.get('mechanism_of_action')]
        if missing_moa:
            self.log_finding(
                "WARNING", "epi_drug_targets", "Missing Data",
                f"{len(missing_moa)} drug-target links missing 'mechanism_of_action'",
                {"link_ids": missing_moa[:10]}  # Sample first 10
            )

        # Check for duplicate links (same drug-target pair)
        pairs = [(l.get('drug_id'), l.get('target_id')) for l in links]
        pair_counts = Counter(pairs)
        duplicates = {str(pair): count for pair, count in pair_counts.items() if count > 1}
        if duplicates:
            self.log_finding(
                "WARNING", "epi_drug_targets", "Duplicates",
                f"Found {len(duplicates)} duplicate drug-target pairs",
                {"duplicates": duplicates}
            )

        print(f"  ✓ Checked {len(links)} drug-target links")

    def audit_epi_indications(self):
        """Audit epi_indications table."""
        print("\n🔍 Auditing epi_indications...")

        response = self.sb.table('epi_indications').select('*').execute()
        indications = response.data
        self.stats['epi_indications_count'] = len(indications)

        # Check for duplicates by name
        names = [i['name'] for i in indications if i.get('name')]
        name_counts = Counter(names)
        duplicates = {name: count for name, count in name_counts.items() if count > 1}
        if duplicates:
            self.log_finding(
                "CRITICAL", "epi_indications", "Duplicates",
                f"Found {len(duplicates)} duplicate indication names",
                {"duplicates": duplicates}
            )

        # Check for missing EFO IDs
        missing_efo = [i['name'] for i in indications if not i.get('efo_id')]
        if missing_efo:
            self.log_finding(
                "WARNING", "epi_indications", "Missing Data",
                f"{len(missing_efo)} indications missing 'efo_id'",
                {"indication_names": missing_efo}
            )

        print(f"  ✓ Checked {len(indications)} indications")

    def audit_epi_drug_indications(self):
        """Audit epi_drug_indications table."""
        print("\n🔍 Auditing epi_drug_indications...")

        response = self.sb.table('epi_drug_indications').select('*').execute()
        links = response.data
        self.stats['epi_drug_indications_count'] = len(links)

        # Check for orphaned drug references
        drug_response = self.sb.table('epi_drugs').select('id').execute()
        valid_drug_ids = {d['id'] for d in drug_response.data}

        orphaned_drugs = [l['id'] for l in links if l.get('drug_id') not in valid_drug_ids]
        if orphaned_drugs:
            self.log_finding(
                "CRITICAL", "epi_drug_indications", "Orphaned Records",
                f"{len(orphaned_drugs)} drug-indication links reference non-existent drugs",
                {"link_ids": orphaned_drugs}
            )

        # Check for orphaned indication references
        indication_response = self.sb.table('epi_indications').select('id').execute()
        valid_indication_ids = {i['id'] for i in indication_response.data}

        orphaned_indications = [l['id'] for l in links if l.get('indication_id') not in valid_indication_ids]
        if orphaned_indications:
            self.log_finding(
                "CRITICAL", "epi_drug_indications", "Orphaned Records",
                f"{len(orphaned_indications)} drug-indication links reference non-existent indications",
                {"link_ids": orphaned_indications}
            )

        # Check approval status distribution
        statuses = Counter([l.get('approval_status', 'unknown') for l in links])
        self.stats['approval_statuses'] = dict(statuses)
        self.log_finding(
            "INFO", "epi_drug_indications", "Data Distribution",
            f"Approval statuses: {dict(statuses)}"
        )

        # Check for duplicate drug-indication pairs
        pairs = [(l.get('drug_id'), l.get('indication_id')) for l in links]
        pair_counts = Counter(pairs)
        duplicates = {str(pair): count for pair, count in pair_counts.items() if count > 1}
        if duplicates:
            self.log_finding(
                "WARNING", "epi_drug_indications", "Duplicates",
                f"Found {len(duplicates)} duplicate drug-indication pairs",
                {"duplicates": duplicates}
            )

        print(f"  ✓ Checked {len(links)} drug-indication links")

    def audit_epi_scores(self):
        """Audit epi_scores table."""
        print("\n🔍 Auditing epi_scores...")

        response = self.sb.table('epi_scores').select('*').execute()
        scores = response.data
        self.stats['epi_scores_count'] = len(scores)

        # Check for orphaned drug references
        drug_response = self.sb.table('epi_drugs').select('id').execute()
        valid_drug_ids = {d['id'] for d in drug_response.data}

        orphaned_drugs = [s['id'] for s in scores if s.get('drug_id') not in valid_drug_ids]
        if orphaned_drugs:
            self.log_finding(
                "CRITICAL", "epi_scores", "Orphaned Records",
                f"{len(orphaned_drugs)} scores reference non-existent drugs",
                {"score_ids": orphaned_drugs}
            )

        # Check for orphaned indication references
        indication_response = self.sb.table('epi_indications').select('id').execute()
        valid_indication_ids = {i['id'] for i in indication_response.data}

        orphaned_indications = [s['id'] for s in scores if s.get('indication_id') not in valid_indication_ids]
        if orphaned_indications:
            self.log_finding(
                "CRITICAL", "epi_scores", "Orphaned Records",
                f"{len(orphaned_indications)} scores reference non-existent indications",
                {"score_ids": orphaned_indications}
            )

        # Check for missing scores
        missing_bio = [s['id'] for s in scores if s.get('bio_score') is None]
        if missing_bio:
            self.log_finding(
                "WARNING", "epi_scores", "Missing Data",
                f"{len(missing_bio)} records missing 'bio_score'",
                {"count": len(missing_bio)}
            )

        missing_chem = [s['id'] for s in scores if s.get('chem_score') is None]
        if missing_chem:
            self.log_finding(
                "INFO", "epi_scores", "Missing Data",
                f"{len(missing_chem)} records missing 'chem_score' (may be expected for early-stage drugs)",
                {"count": len(missing_chem)}
            )

        missing_tract = [s['id'] for s in scores if s.get('tractability_score') is None]
        if missing_tract:
            self.log_finding(
                "WARNING", "epi_scores", "Missing Data",
                f"{len(missing_tract)} records missing 'tractability_score'",
                {"count": len(missing_tract)}
            )

        missing_total = [s['id'] for s in scores if s.get('total_score') is None]
        if missing_total:
            self.log_finding(
                "CRITICAL", "epi_scores", "Missing Data",
                f"{len(missing_total)} records missing 'total_score'",
                {"score_ids": missing_total}
            )

        # Check for score outliers (outside 0-100 range)
        outliers = []
        for s in scores:
            for field in ['bio_score', 'chem_score', 'tractability_score', 'total_score']:
                val = s.get(field)
                if val is not None and (val < 0 or val > 100):
                    outliers.append({
                        "score_id": s['id'],
                        "field": field,
                        "value": val
                    })

        if outliers:
            self.log_finding(
                "CRITICAL", "epi_scores", "Invalid Data",
                f"{len(outliers)} score values outside 0-100 range",
                {"outliers": outliers}
            )

        # Calculate score statistics
        bio_scores = [s['bio_score'] for s in scores if s.get('bio_score') is not None]
        if bio_scores:
            self.stats['bio_score_avg'] = round(sum(bio_scores) / len(bio_scores), 1)
            self.stats['bio_score_min'] = round(min(bio_scores), 1)
            self.stats['bio_score_max'] = round(max(bio_scores), 1)

        total_scores = [s['total_score'] for s in scores if s.get('total_score') is not None]
        if total_scores:
            self.stats['total_score_avg'] = round(sum(total_scores) / len(total_scores), 1)
            self.stats['total_score_min'] = round(min(total_scores), 1)
            self.stats['total_score_max'] = round(max(total_scores), 1)

        print(f"  ✓ Checked {len(scores)} score records")

    def audit_chembl_metrics(self):
        """Audit chembl_metrics table."""
        print("\n🔍 Auditing chembl_metrics...")

        response = self.sb.table('chembl_metrics').select('*').execute()
        metrics = response.data
        self.stats['chembl_metrics_count'] = len(metrics)

        # Check for orphaned drug references
        drug_response = self.sb.table('epi_drugs').select('id').execute()
        valid_drug_ids = {d['id'] for d in drug_response.data}

        orphaned_drugs = [m['id'] for m in metrics if m.get('drug_id') not in valid_drug_ids]
        if orphaned_drugs:
            self.log_finding(
                "CRITICAL", "chembl_metrics", "Orphaned Records",
                f"{len(orphaned_drugs)} metrics reference non-existent drugs",
                {"metric_ids": orphaned_drugs}
            )

        # Check for missing potency
        missing_potency = [m['id'] for m in metrics if m.get('best_potency_nm') is None]
        if missing_potency:
            self.log_finding(
                "WARNING", "chembl_metrics", "Missing Data",
                f"{len(missing_potency)} metrics missing 'best_potency_nm'",
                {"count": len(missing_potency)}
            )

        # Check for invalid selectivity (should be >= 0)
        invalid_selectivity = []
        for m in metrics:
            val = m.get('selectivity_delta_log')
            if val is not None and val < 0:
                invalid_selectivity.append({
                    "metric_id": m['id'],
                    "value": val
                })

        if invalid_selectivity:
            self.log_finding(
                "WARNING", "chembl_metrics", "Invalid Data",
                f"{len(invalid_selectivity)} metrics have negative selectivity_delta_log",
                {"samples": invalid_selectivity[:5]}
            )

        # Check richness distribution
        richness_values = [m.get('richness_count', 0) for m in metrics]
        if richness_values:
            self.stats['chembl_richness_avg'] = round(sum(richness_values) / len(richness_values), 1)
            self.stats['chembl_richness_max'] = max(richness_values)

        print(f"  ✓ Checked {len(metrics)} ChEMBL metrics")

    def audit_epi_combos(self):
        """Audit epi_combos table."""
        print("\n🔍 Auditing epi_combos...")

        response = self.sb.table('epi_combos').select('*').execute()
        combos = response.data
        self.stats['epi_combos_count'] = len(combos)

        # Check for duplicate combo strategies
        strategies = [c.get('combo_strategy') for c in combos if c.get('combo_strategy')]
        strategy_counts = Counter(strategies)
        duplicates = {strat: count for strat, count in strategy_counts.items() if count > 1}
        if duplicates:
            self.log_finding(
                "WARNING", "epi_combos", "Duplicates",
                f"Found {len(duplicates)} duplicate combo strategies",
                {"duplicates": duplicates}
            )

        # Check for missing rationale
        missing_rationale = [c.get('combo_strategy') for c in combos if not c.get('rationale')]
        if missing_rationale:
            self.log_finding(
                "WARNING", "epi_combos", "Missing Data",
                f"{len(missing_rationale)} combos missing 'rationale'",
                {"strategies": missing_rationale}
            )

        # Check category distribution
        categories = Counter([c.get('category', 'unknown') for c in combos])
        self.stats['combo_categories'] = dict(categories)
        self.log_finding(
            "INFO", "epi_combos", "Data Distribution",
            f"Combo categories: {dict(categories)}"
        )

        print(f"  ✓ Checked {len(combos)} combination strategies")

    def audit_signatures(self):
        """Audit epi_signatures and epi_signature_targets tables."""
        print("\n🔍 Auditing signature tables...")

        # Check signatures
        sig_response = self.sb.table('epi_signatures').select('*').execute()
        signatures = sig_response.data
        self.stats['epi_signatures_count'] = len(signatures)

        # Check signature-target links
        link_response = self.sb.table('epi_signature_targets').select('*').execute()
        links = link_response.data
        self.stats['epi_signature_targets_count'] = len(links)

        # Check for orphaned signature references
        valid_sig_ids = {s['id'] for s in signatures}
        orphaned_sigs = [l['id'] for l in links if l.get('signature_id') not in valid_sig_ids]
        if orphaned_sigs:
            self.log_finding(
                "CRITICAL", "epi_signature_targets", "Orphaned Records",
                f"{len(orphaned_sigs)} signature-target links reference non-existent signatures",
                {"link_ids": orphaned_sigs}
            )

        # Check for orphaned target references
        target_response = self.sb.table('epi_targets').select('id').execute()
        valid_target_ids = {t['id'] for t in target_response.data}
        orphaned_targets = [l['id'] for l in links if l.get('target_id') not in valid_target_ids]
        if orphaned_targets:
            self.log_finding(
                "CRITICAL", "epi_signature_targets", "Orphaned Records",
                f"{len(orphaned_targets)} signature-target links reference non-existent targets",
                {"link_ids": orphaned_targets}
            )

        print(f"  ✓ Checked {len(signatures)} signatures and {len(links)} signature-target links")

    def generate_report(self) -> str:
        """Generate comprehensive audit report."""
        report_lines = []

        report_lines.append("=" * 80)
        report_lines.append("DATABASE INTEGRITY AUDIT REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Database: pilldreams (Supabase)")
        report_lines.append("")

        # Executive Summary
        report_lines.append("EXECUTIVE SUMMARY")
        report_lines.append("-" * 80)
        critical_count = sum(1 for f in self.findings if f['severity'] == 'CRITICAL')
        warning_count = sum(1 for f in self.findings if f['severity'] == 'WARNING')
        info_count = sum(1 for f in self.findings if f['severity'] == 'INFO')

        report_lines.append(f"Total Findings: {len(self.findings)}")
        report_lines.append(f"  - CRITICAL: {critical_count}")
        report_lines.append(f"  - WARNING:  {warning_count}")
        report_lines.append(f"  - INFO:     {info_count}")
        report_lines.append("")

        # Database Statistics
        report_lines.append("DATABASE STATISTICS")
        report_lines.append("-" * 80)
        for key, value in sorted(self.stats.items()):
            report_lines.append(f"  {key}: {value}")
        report_lines.append("")

        # Findings by Severity
        for severity in ['CRITICAL', 'WARNING', 'INFO']:
            severity_findings = [f for f in self.findings if f['severity'] == severity]
            if not severity_findings:
                continue

            report_lines.append("")
            report_lines.append(f"{severity} FINDINGS ({len(severity_findings)})")
            report_lines.append("=" * 80)

            # Group by table
            by_table = {}
            for f in severity_findings:
                table = f['table']
                if table not in by_table:
                    by_table[table] = []
                by_table[table].append(f)

            for table in sorted(by_table.keys()):
                report_lines.append(f"\n{table}")
                report_lines.append("-" * 80)

                for finding in by_table[table]:
                    report_lines.append(f"\n  [{finding['category']}] {finding['message']}")
                    if finding.get('details'):
                        # Format details nicely
                        details = finding['details']
                        if isinstance(details, dict):
                            for k, v in details.items():
                                # Truncate long lists
                                if isinstance(v, list) and len(v) > 10:
                                    v = v[:10] + [f"... ({len(v) - 10} more)"]
                                report_lines.append(f"    {k}: {v}")

        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append("END OF REPORT")
        report_lines.append("=" * 80)

        return "\n".join(report_lines)

    def run_full_audit(self):
        """Run complete audit of all tables."""
        print("🔎 Starting Database Integrity Audit...\n")

        try:
            self.audit_epi_targets()
            self.audit_epi_drugs()
            self.audit_epi_drug_targets()
            self.audit_epi_indications()
            self.audit_epi_drug_indications()
            self.audit_epi_scores()
            self.audit_chembl_metrics()
            self.audit_epi_combos()
            self.audit_signatures()

            print("\n✅ Audit complete! Generating report...\n")

            report = self.generate_report()

            # Save to file
            output_path = "database_audit_report.txt"
            with open(output_path, 'w') as f:
                f.write(report)

            print(f"📄 Report saved to: {output_path}\n")
            print(report)

        except Exception as e:
            print(f"\n❌ Audit failed: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    auditor = DatabaseAuditor()
    auditor.run_full_audit()
