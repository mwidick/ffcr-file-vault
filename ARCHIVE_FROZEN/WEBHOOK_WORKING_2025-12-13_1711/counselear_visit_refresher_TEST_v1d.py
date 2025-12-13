"""
CounselEAR MRN Refresher – TEST v1d

Wrapper that:
- Chooses which core module to use
- Points to the Test MRN CSV
- Calls core.run_mrn_refresh(...)

Switch cores by editing the import section only.
"""

# ---------------------------------------------------------------------------
# Choose core implementation
# ---------------------------------------------------------------------------

# Patched core that clicks into the first SearchResults patient row
import counselear_visit_refresher_core_v2_GoldCore_OPENPAT_v4 as core



# Stable baseline – last-known working pattern (no patient-row click)
# import counselear_visit_refresher_core_v2_GoldCore as core

# Experimental version with SearchResults → detail-page → real Save
# import counselear_visit_refresher_core_v2_SaveDrill_v1 as core


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    mrn_csv = r"C:\FFCR_Project\Counselear Project\Target_MRNs_Test.csv"
    core.run_mrn_refresh(mrn_csv, mode_label="TEST")


if __name__ == "__main__":
    main()
