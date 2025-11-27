"""
Update NBI Member Flag in Database

Reads the NBI companies from data/nbi_companies.csv and marks them
as is_nbi_member=true in the company table.

Uses fuzzy name matching since NBI list has short names like "Vertex"
while database has full names like "Vertex Pharmaceuticals, Inc."
"""

import os
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
import structlog
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from core.supabase_client import get_client

load_dotenv()
logger = structlog.get_logger()


# Manual ticker mapping for NBI companies that are hard to match
# Format: NBI name -> ticker
NBI_TICKER_MAP = {
    # Major companies
    "Vertex": "VRTX",
    "Gilead": "GILD",
    "Amgen": "AMGN",
    "Biogen": "BIIB",
    "Illumina": "ILMN",
    "Viatris": "VTRS",
    "Ionis Pharma": "IONS",
    "ACADIA": "ACAD",
    "Alkermes Plc": "ALKS",
    "Alnylam": "ALNY",
    "Arrowhead Pharma": "ARWR",
    "Vericel Corp Ord": "VCEL",
    "Sarepta": "SRPT",
    "BioCryst": "BCRX",
    "Biomarin Pharma": "BMRN",
    "Codexis": "CDXS",
    "Cytokinetics Inc": "CYTK",
    "Dynavax": "DVAX",
    "Avadel Pharma": "AVDL",
    "Amicus": "FOLD",
    "Geron": "GERN",
    "Grifols ADR": "GRFS",
    "Halozyme": "HALO",
    "Incyte": "INCY",
    "Insmed": "INSM",
    "Amneal Pharma A": "AMRX",
    "Ironwood": "IRWD",
    "Jazz Pharma": "JAZZ",
    "Ligand": "LGND",
    "Lexicon": "LXRX",
    "MannKind": "MNKD",
    "Neurocrine": "NBIX",
    "Novavax": "NVAX",
    "Omeros": "OMER",
    "Pacific Biosciences": "PACB",
    "Pacira": "PCRX",
    "Eyepoint Pharma": "EYPT",
    "Rigel": "RIGL",
    "SIGA Tech": "SIGA",
    "Madrigal Pharma": "MDGL",
    "Innoviva": "INVA",
    "Vanda": "VNDA",
    "Sanofi ADR": "SNY",
    "Altimmune": "ALT",
    "Savara": "SVRA",
    "CorMedix": "CRMD",
    "Supernus": "SUPN",
    "Arbutus Biopharma": "ABUS",
    "United Therapeutics": "UTHR",
    "Regeneron Pharma": "REGN",
    "ANI Pharma": "ANIP",
    "Amarin": "AMRN",
    "Exelixis": "EXEL",
    "AstraZeneca ADR": "AZN",
    "Prothena": "PRTA",
    "Harrow Health": "HROW",
    "Arcturus Therapeutics Holdings Inc": "ARCT",
    "Enanta": "ENTA",
    "Precigen": "PGEN",
    "Agios Pharm": "AGIO",
    "Esperion": "ESPR",
    "Fate Therapeutics": "FATE",
    "PTC Therapeutics": "PTCT",
    "MacroGenics Inc": "MGNX",
    "Veracyte Inc": "VCYT",
    "Xencor Inc": "XNCR",
    "Anavex Life Sciences": "AVXL",
    "Iovance Biotherapeutics": "IOVA",
    "Neurogene": "NGNE",
    "Uniqure NV": "QURE",
    "Travere Therapeutics": "TVTX",
    "Ultragenyx": "RARE",
    "Phibro": "PAHC",
    "Amphastar P": "AMPH",
    "Ardelyx Inc": "ARDX",
    "Theravance Biopharma": "TBPH",
    "Larimar Therapeutics Inc": "LRMR",
    "Ocular Therapeutix Inc": "OCUL",
    "Aurinia Pharma": "AUPH",
    "Genmab AS": "GMAB",
    "Mesoblast": "MESO",
    "ADMA Biologics Inc": "ADMA",
    "Xenon Pharmaceuticals": "XENE",
    "Ascendis Pharma AS": "ASND",
    "Rocket Pharma": "RCKT",
    "Summit Therapeutics PLC": "SMMT",
    "Kalvista Pharma": "KALV",
    "Zevra Therapeutics": "ZVRA",
    "Collegium Pharmaceutical": "COLL",
    "Galapagos ADR": "GLPG",
    "Astria Therapeutics": "ATXS",
    "Immunitybio Inc": "IBRX",
    "Novocure Ltd": "NVCR",
    "Regenxbio Inc": "RGNX",
    "Kura Oncology Inc": "KURA",
    "Axsome Therapeutics Inc": "AXSM",
    "Voyager Therapeutics Inc": "VYGR",
    "Wave Life Sciences Ltd": "WVE",
    "BeOne Medicines DRC": "ONC",
    "Corvus Pharmaceuticals": "CRVS",
    "Editas Medicine": "EDIT",
    "HUTCHMED DRC": "HCM",
    "Syndax Pharmaceuticals": "SNDX",
    "Spyre Therapeutics": "SYRE",
    "Merus": "MRUS",
    "Intellia Therapeutics Inc": "NTLA",
    "Cartesian Therapeutics": "RNAC",
    "Medpace Holdings": "MEDP",
    "Protagonist Therapeutics": "PTGX",
    "AC Immune": "ACIU",
    "Crispr Therapeutics": "CRSP",
    "AnaptysBio": "ANAB",
    "Zymeworks": "ZYME",
    "UroGen Pharma": "URGN",
    "argenx ADR": "ARGX",
    "Mersana Therapeutics": "MRSN",
    "Krystal Biotech": "KRYS",
    "Zai Lab": "ZLAB",
    "Rhythm Pharma": "RYTM",
    "Apellis Pharma": "APLS",
    "Denali Therapeutics": "DNLI",
    "Solid Biosciences": "SLDB",
    "Evolus": "EOLS",
    "Q32 Bio": "QTTB",
    "Cogent Biosciences": "COGT",
    "Kiniksa Pharma": "KNSA",
    "Scholar Rock": "SRRK",
    "MeiraGTx": "MGTX",
    "Xeris Pharmaceuticals": "XERS",
    "Tectonic Therapeutic": "TECX",
    "Autolus Therapeutics": "AUTL",
    "Replimune": "REPL",
    "Aquestive Therapeutics": "AQST",
    "Crinetics Pharma": "CRNX",
    "Sutro Biopharma": "STRO",
    "Arvinas": "ARVN",
    "Guardant Health": "GH",
    "Allogene Therapeutics": "ALLO",
    "Twist Bioscience": "TWST",
    "Moderna": "MRNA",
    "Alector": "ALEC",
    "Trevi Therapeutics": "TRVI",
    "Applied Therapeutics": "APLT",
    "Ideaya Biosciences": "IDYA",
    "Bicycle Therapeutics": "BCYC",
    "Akero Therapeutics": "AKRO",
    "Stoke Therapeutics": "STOK",
    "Personalis": "PSNL",
    "BridgeBio Pharma": "BBIO",
    "Adaptive Biotechnologies": "ADPT",
    "Mirum Pharmaceuticals": "MIRM",
    "Castle Biosciences": "CSTL",
    "10X Genomics": "TXG",
    "BioNTech": "BNTX",
    "Vir Biotech": "VIR",
    "Phathom Pharma": "PHAT",
    "Arcutis": "ARQT",
    "Beam": "BEAM",
    "Revolution Med": "RVMD",
    "Enliven Therapeutics": "ELVN",
    "Mind Medicine": "MNMD",
    "Keros": "KROS",
    "Oric Pharma": "ORIC",
    "Immunovant": "IMVT",
    "Pliant": "PLRX",
    "Legend Bio": "LEGN",
    "Avidity Bio": "RNA",
    "Vaxcyte": "PCVX",
    "Royalty Pharma": "RPRX",
    "Nkarta": "NKTX",
    "Relay": "RLAY",
    "Annexon": "ANNX",
    "Nurix": "NRIX",
    "CureVac NV": "CVAC",
    "Disc Medicine": "IRON",
    "Harmony Bio": "HRMY",
    "Kymera": "KYMR",
    "Tango Therapeutics": "TNGX",
    "Dyne": "DYN",
    "Compass Pathways": "CMPS",
    "Taysha Gene": "TSHA",
    "Silence Therapeutics": "SLN",
    "C4": "CCCC",
    "Praxis Precision": "PRAX",
    "Tarsus": "TARS",
    "Foghorn": "FHTX",
    "Atea": "AVIR",
    "Maravai Lifesciences": "MRVI",
    "Olema": "OLMA",
    "ARS Pharmaceuticals": "SPRY",
    "4D Molecular": "FDMT",
    "Abcellera Biologics": "ABCL",
    "Cullinan Oncology LLC": "CGEM",
    "Sana Biotechnology": "SANA",
    "Immunocore Holdings": "IMCR",
    "Terns Pharmaceuticals": "TERN",
    "NewAmsterdam Pharma": "NAMS",
    "Roivant Sciences": "ROIV",
    "Humacyte": "HUMA",
    "Design Therapeutics": "DSGN",
    "Edgewise Therapeutics": "EWTX",
    "Onkure Therapeutics": "OKUR",
    "Biomea Fusion": "BMEA",
    "Recursion Pharmaceuticals": "RXRX",
    "Vera Therapeutics": "VERA",
    "Centessa Pharmaceuticals": "CNTA",
    "Day One Biopharmaceuticals": "DAWN",
    "Janux Therapeutics": "JANX",
    "Lyell Immunopharma": "LYEL",
    "Alpha Teknova": "TKNO",
    "LENZ Therapeutics": "LENZ",
    "Monte Rosa Therapeutics": "GLUE",
    "Erasca": "ERAS",
    "Tscan Therapeutics": "TCRX",
    "Absci": "ABSI",
    "Nuvalent": "NUVL",
    "MaxCyte": "MXCT",
    "Climb Bio": "CLYM",
    "Tyra Biosciences": "TYRA",
    "OmniAb": "OABI",
    "Pyxis Oncology": "PYXS",
    "Aura Biosciences": "APTS",
    "Entrada Therapeutics": "TRDA",
    "Amylyx Pharmaceuticals": "AMLX",
    "Tevogen Bio Holdings": "TVGN",
    "Arcellx": "ACLX",
    "PepGen": "PEPG",
    "Alvotech": "ALVO",
    "Prime Medicine": "PRME",
    "Acrivon Therapeutics": "ACRV",
    "Mineralys Therapeutics": "MLYS",
    "Structure Therapeutics ADR": "GPCR",
    "Indivior": "INDV",
    "Fortrea Holdings": "FTRE",
    "Apogee Therapeutics": "APGE",
    "Neumora Therapeutics": "NMRA",
    "Lexeo Therapeutics": "LXEO",
    "CG Oncology": "CGON",
    "Arrivent Biopharma": "AVBP",
    "Kyverna Therapeutics": "KYTX",
    "Inhibrx Biosciences": "INBX",
    "Rapport Therapeutics": "RAPP",
    "Tempus AI": "TEM",
    "Grail": "GRAL",
    "Alumis": "ALMS",
    "Artiva Biotherapeutics": "ARTV",
    "Oruka Therapeutics": "ORKA",
}


def load_nbi_companies() -> list:
    """Load NBI company names from CSV file."""
    csv_path = Path(__file__).parent.parent / "data" / "nbi_companies.csv"

    # Read file and extract just the company names (first column before comma)
    names = []
    with open(csv_path, 'r') as f:
        lines = f.readlines()
        for line in lines[1:]:  # Skip header
            line = line.strip()
            if line and ',' in line:
                name = line.split(',')[0]
                if name:
                    names.append(name)

    logger.info(f"Loaded {len(names)} NBI company names from CSV")
    return names


def update_nbi_members():
    """Update is_nbi_member flag for NBI companies in database."""
    db = get_client()
    nbi_names = load_nbi_companies()

    # First, reset all companies to is_nbi_member = false
    logger.info("Resetting all companies to is_nbi_member = false")
    try:
        db.client.table('company').update({
            'is_nbi_member': False,
            'updated_at': datetime.now().isoformat()
        }).neq('id', '00000000-0000-0000-0000-000000000000').execute()
    except Exception as e:
        logger.warning(f"Could not reset all companies: {e}")

    # Now update NBI members
    updated = 0
    not_found = []

    for nbi_name in nbi_names:
        # Skip empty names
        if not nbi_name or not nbi_name.strip():
            continue

        # Look up ticker from manual mapping
        ticker = NBI_TICKER_MAP.get(nbi_name)

        if not ticker:
            logger.warning(f"No ticker mapping for: {nbi_name}")
            not_found.append(nbi_name)
            continue

        # Update in database
        try:
            result = db.client.table('company').update({
                'is_nbi_member': True,
                'updated_at': datetime.now().isoformat()
            }).eq('ticker', ticker).execute()

            if result.data:
                updated += 1
                logger.info(f"Updated {ticker} ({nbi_name}) as NBI member")
            else:
                # Company might not exist in database yet
                logger.warning(f"Ticker {ticker} ({nbi_name}) not found in database")
                not_found.append(f"{nbi_name} ({ticker})")

        except Exception as e:
            logger.error(f"Failed to update {ticker}: {e}")
            not_found.append(f"{nbi_name} ({ticker})")

    logger.info(f"Updated {updated} companies as NBI members")

    if not_found:
        logger.warning(f"Not found in database: {len(not_found)} companies")
        for name in not_found[:20]:  # Show first 20
            logger.warning(f"  - {name}")

    return updated, not_found


def verify_nbi_members():
    """Verify NBI member count in database."""
    db = get_client()

    result = db.client.table('company').select('ticker, name').eq('is_nbi_member', True).execute()

    nbi_count = len(result.data)
    logger.info(f"Total NBI members in database: {nbi_count}")

    # Show sample
    logger.info("Sample NBI members:")
    for company in result.data[:10]:
        logger.info(f"  {company['ticker']}: {company['name']}")

    return result.data


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Update NBI member flags in database")
    parser.add_argument("--verify", action="store_true", help="Verify NBI member count")
    parser.add_argument("--update", action="store_true", help="Update NBI members")

    args = parser.parse_args()

    if args.verify:
        verify_nbi_members()
    elif args.update:
        updated, not_found = update_nbi_members()
        print(f"\nUpdated {updated} companies as NBI members")
        print(f"Not found: {len(not_found)} companies")
    else:
        # Default: update
        updated, not_found = update_nbi_members()
        print(f"\nUpdated {updated} companies as NBI members")
        print(f"Not found: {len(not_found)} companies")
