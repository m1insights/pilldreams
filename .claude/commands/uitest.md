# UI Testing Command

Run comprehensive UI testing using Playwright on the specified page or flow.

## Instructions

Use the `playwright-ui-tester` agent to perform UI testing on the pilldreams frontend.

**Target URL Base**: http://localhost:3000

**User Request**: $ARGUMENTS

## Testing Scope

If no specific page is mentioned, test the following key pages:
1. Homepage (/)
2. Watchlist (/watchlist)
3. Explore pages (/explore/drugs, /explore/targets, /explore/editing, /explore/combos, /explore/patents, /explore/news, /explore/companies)
4. Calendar (/calendar)
5. Settings/Billing (/settings/billing)

## Test Categories

For each page, verify:
- All navigation links work correctly
- Buttons are clickable and respond appropriately
- Forms (if any) accept input and validate correctly
- Dropdowns and select menus function
- Modals open and close properly
- Data tables load and sort correctly
- Score badges and visual elements render
- Mobile responsiveness (if specified)

## Reporting

After testing, provide:
1. Summary of pages tested
2. List of any broken links or non-functional elements
3. Screenshots of any failures
4. Recommendations for fixes
