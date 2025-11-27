import os
import shutil

def cleanup():
    archive_dir = "legacy_archive"
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
        print(f"Created {archive_dir}")

    # 1. Move Directories
    dirs_to_move = [
        "ingestion", "agents", "aceternity-marketing", "landing", 
        "mcp_servers", "data", "articles"
    ]
    
    for d in dirs_to_move:
        if os.path.exists(d):
            shutil.move(d, os.path.join(archive_dir, d))
            print(f"Moved directory {d}")

    # 2. Move Root Files
    files_to_move = [
        "check_data_completeness.py", "check_data_quality.py", "check_junction.py", 
        "check_total_trials.py", "spot_check.py", "test_deduplication.py", 
        "verify_finance_tab.py", "verify_science_tab.py", "verify_agents_new.py", 
        "debug_gemini.py", "debug_ot.py", "debug_search.py", "run_full_ingestion.sh",
        "requirements.txt"
    ]
    
    # Also move logs and txt results
    for f in os.listdir("."):
        if (f.endswith(".log") or f.endswith(".txt")) and f != "requirements.txt": # requirements.txt is in list above
            files_to_move.append(f)

    for f in files_to_move:
        if os.path.exists(f):
            shutil.move(f, os.path.join(archive_dir, f))
            print(f"Moved file {f}")

    # 3. Clean up 'core'
    # We want to keep core/schema_pivot.sql, move everything else.
    if os.path.exists("core"):
        core_archive = os.path.join(archive_dir, "core")
        if not os.path.exists(core_archive):
            os.makedirs(core_archive)
        
        for f in os.listdir("core"):
            if f != "schema_pivot.sql":
                src = os.path.join("core", f)
                dst = os.path.join(core_archive, f)
                shutil.move(src, dst)
                print(f"Moved core/{f}")

    # 4. Clean up 'app'
    # We want to keep app/main.py, move everything else.
    if os.path.exists("app"):
        app_archive = os.path.join(archive_dir, "app")
        if not os.path.exists(app_archive):
            os.makedirs(app_archive)
            
        for f in os.listdir("app"):
            if f != "main.py":
                src = os.path.join("app", f)
                dst = os.path.join(app_archive, f)
                shutil.move(src, dst)
                print(f"Moved app/{f}")

    print("Cleanup complete. Legacy files moved to legacy_archive/")

if __name__ == "__main__":
    cleanup()
