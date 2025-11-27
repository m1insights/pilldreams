"""
Add Missing NBI Companies to Database

Adds the NBI companies that weren't found in our original NASDAQ keyword-based list.
These are companies that either:
1. Don't match biopharma keywords in their names
2. Are on other exchanges (ADRs, etc.)
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import structlog
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent.parent))

from core.supabase_client import get_client

load_dotenv()
logger = structlog.get_logger()

# Missing NBI companies with their full names
MISSING_NBI_COMPANIES = {
    "ILMN": "Illumina, Inc.",
    "VTRS": "Viatris Inc.",
    "ALKS": "Alkermes plc",
    "GERN": "Geron Corporation",
    "GRFS": "Grifols, S.A.",
    "INSM": "Insmed Incorporated",
    "NVAX": "Novavax, Inc.",
    "OMER": "Omeros Corporation",
    "SIGA": "SIGA Technologies, Inc.",
    "INVA": "Innoviva, Inc.",
    "SNY": "Sanofi",
    "ALT": "Altimmune, Inc.",
    "SVRA": "Savara, Inc.",
    "CRMD": "CorMedix Inc.",
    "AMRN": "Amarin Corporation plc",
    "AZN": "AstraZeneca PLC",
    "HROW": "Harrow Health, Inc.",
    "PGEN": "Precigen, Inc.",
    "MGNX": "MacroGenics, Inc.",
    "VCYT": "Veracyte, Inc.",
    "XNCR": "Xencor, Inc.",
    "AVXL": "Anavex Life Sciences Corp.",
    "QURE": "uniQure N.V.",
    "PAHC": "Phibro Animal Health Corporation",
    "ARDX": "Ardelyx, Inc.",
    "GMAB": "Genmab A/S",
    "MESO": "Mesoblast Limited",
    "GLPG": "Galapagos NV",
    "NVCR": "NovoCure Limited",
    "WVE": "Wave Life Sciences Ltd.",
    "EDIT": "Editas Medicine, Inc.",
    "HCM": "HUTCHMED (China) Limited",
    "MEDP": "Medpace Holdings, Inc.",
    "ACIU": "AC Immune SA",
    "ZYME": "Zymeworks Inc.",
    "ARGX": "argenx SE",
    "ZLAB": "Zai Lab Limited",
    "EOLS": "Evolus, Inc.",
    "SRRK": "Scholar Rock Holding Corporation",
    "MGTX": "MeiraGTx Holdings plc",
    "REPL": "Replimune Group, Inc.",
    "ARVN": "Arvinas, Inc.",
    "GH": "Guardant Health, Inc.",
    "ALEC": "Alector, Inc.",
    "PSNL": "Personalis, Inc.",
    "MNMD": "Mind Medicine Inc.",
    "NKTX": "Nkarta, Inc.",
    "ANNX": "Annexon, Inc.",
    "CVAC": "CureVac N.V.",
    "IRON": "Disc Medicine, Inc.",
    "CMPS": "COMPASS Pathways plc",
    "MRVI": "Maravai LifeSciences Holdings, Inc.",
    "ROIV": "Roivant Sciences Ltd.",
    "HUMA": "Humacyte, Inc.",
    "TKNO": "Alpha Teknova, Inc.",
    "ERAS": "Erasca, Inc.",
    "ABSI": "Absci Corporation",
    "NUVL": "Nuvalent, Inc.",
    "MXCT": "MaxCyte, Inc.",
    "OABI": "OmniAb, Inc.",
    "APTS": "Aura Biosciences, Inc.",
    "ACLX": "Arcellx, Inc.",
    "PEPG": "PepGen Inc.",
    "ALVO": "Alvotech",
    "PRME": "Prime Medicine, Inc.",
    "INDV": "Indivior PLC",
    "FTRE": "Fortrea Holdings Inc.",
    "TEM": "Tempus AI, Inc.",
    "GRAL": "GRAIL, Inc.",
    "ALMS": "Alumis Inc.",
}


def add_missing_companies():
    """Add missing NBI companies to the database."""
    db = get_client()
    added = 0

    for ticker, name in MISSING_NBI_COMPANIES.items():
        try:
            # Upsert company (insert or update if exists)
            db.client.table('company').upsert({
                'ticker': ticker,
                'name': name,
                'exchange': 'NASDAQ',  # Some may be NYSE but defaulting to NASDAQ
                'is_nbi_member': True,
                'updated_at': datetime.now().isoformat()
            }, on_conflict='ticker').execute()

            added += 1
            logger.info(f"Added/updated {ticker}: {name}")

        except Exception as e:
            logger.error(f"Failed to add {ticker}: {e}")

    logger.info(f"Added/updated {added} missing NBI companies")
    return added


def verify_total_nbi():
    """Verify total NBI count after adding missing companies."""
    db = get_client()

    result = db.client.table('company').select('ticker, name').eq('is_nbi_member', True).execute()

    nbi_count = len(result.data)
    logger.info(f"Total NBI members in database: {nbi_count}")

    return nbi_count


if __name__ == "__main__":
    added = add_missing_companies()
    print(f"\nAdded {added} missing NBI companies")

    total = verify_total_nbi()
    print(f"Total NBI members now: {total}")
