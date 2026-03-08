**GPToutfit**

**Handoff 8 --- UX & AI Companion Enhancements**

*For Claude Code · v1.0 · March 7, 2026*

**Overview & Scope**

This handoff defines 5 improvements to the current AI Wardrobe & AI
Stylist interface, derived from UX review of the live MVP. The changes
span three layers: (1) UI component fixes, (2) wardrobe management
actions, and (3) a new AI Companion feature that evaluates the user\'s
outfit selection in context.

All changes operate on the existing frontend + backend architecture. No
new external services are required except the GPT-4o-mini API call for
the AI Companion, which follows the same pattern as the existing
guardrail validation call.

**Change 1 --- Add to Wardrobe Button Redesign**

**Problem**

The current add-to-wardrobe control overlaps with the \'Low Stock\'
badge (visible in screenshot). The action is not clearly labelled,
making it unintuitive for first-time users.

**Solution**

Move the add-to-wardrobe action out of the image overlay and into a
dedicated CTA row below the card image. Use an explicit text label.

**Visual Layout --- Result Card (after change)**

Each item card in AI Stylist results AND Discover results must follow
this structure:

> ┌────────────────────────────┐
>
> │ \[product image\] │
>
> │ \[Low Stock\]│ ← badge stays top-right, inside image
>
> ├────────────────────────────┤
>
> │ Product Name │ ← product name
>
> │ Category · Gender │ ← metadata row
>
> │ £ Price │ ← price
>
> │ \[+ Add to Wardrobe\] │ ← full-width button, below all text
>
> └────────────────────────────┘

**Button Specifications**

  --------------- -------------- --------------------------------------------
  **Requirement   **Priority**   **Description**
  ID**                           

  H8-01-A         HIGH           Add a full-width \'+ Add to Wardrobe\'
                                 button as the LAST element inside each
                                 result card, below name, category, and
                                 price. The button must NOT overlap any badge
                                 or image element.

  H8-01-B         HIGH           Badge positioning: \'Low Stock\' (and any
                                 other badges) remain absolutely positioned
                                 top-right WITHIN the image container only.
                                 They must have z-index lower than the image
                                 overlay hover state.

  H8-01-C         MEDIUM         Button state: when item is already in
                                 wardrobe, change label to \'✓ In Wardrobe\'
                                 with a muted/grey style. Clicking again
                                 removes the item from wardrobe (toggle
                                 behaviour).

  H8-01-D         MEDIUM         On tap/click, show a brief toast
                                 notification: \'Added to Wardrobe ✓\' (2s,
                                 bottom-center). This applies to cards in
                                 both AI Stylist results and Discover
                                 results.
  --------------- -------------- --------------------------------------------

**Change 2 --- Wardrobe Management: Clear & Delete Actions**

**Problem**

Once items are in My Wardrobe, there is no way to reset or selectively
remove them. Users who want to start over or remove a mistake have no
recourse.

**Solution**

Add two management actions to the My Wardrobe panel: a bulk \'Clear
All\' and per-item removal. Additionally support clearing only selected
items.

**UI Placement**

In the My Wardrobe tab header row (same row as the item count badge and
total price):

- Right-align a \'Manage\' button that toggles selection mode

- In selection mode: each card shows a checkbox overlay; a \'Remove
  Selected\' button appears in the header

- A separate \'Clear All\' text link (danger style, red) appears at the
  far right of the header, always visible

  --------------- -------------- --------------------------------------------
  **Requirement   **Priority**   **Description**
  ID**                           

  H8-02-A         HIGH           Add a \'Clear All\' button to the My
                                 Wardrobe section header. On click, show a
                                 confirmation modal: \'Remove all X items
                                 from your wardrobe? This cannot be undone.\'
                                 with \[Cancel\] and \[Clear All\] buttons.

  H8-02-B         HIGH           Add a \'Manage\' toggle button. When active,
                                 each wardrobe card shows a checkbox in the
                                 top-left corner. The total price row is
                                 hidden while in manage mode.

  H8-02-C         HIGH           While in manage mode, show a \'Remove
                                 Selected (N)\' button in the header that
                                 removes only the checked items. N updates
                                 dynamically as checkboxes are ticked.

  H8-02-D         MEDIUM         Individual card removal: each card always
                                 has a small \'×\' icon in the top-right
                                 corner (outside manage mode too) to remove
                                 that single item without entering manage
                                 mode.

  H8-02-E         LOW            After any removal action, animate the
                                 remaining cards to reflow smoothly (CSS
                                 transition). Update total price and item
                                 count badge immediately.
  --------------- -------------- --------------------------------------------

**Change 3 --- Discover Also Adds to Wardrobe**

**Context**

Currently, the Discover tab allows browsing catalog items by occasion
but the path to saving items to the wardrobe is unclear. This change
makes the Discover tab a first-class source for the wardrobe, using the
same card component and add button defined in Change 1.

**Solution**

Discover item cards must use the identical card component as AI Stylist
results. The \'+ Add to Wardrobe\' button (H8-01-A) applies here too ---
no separate implementation needed if the card component is properly
shared.

  --------------- -------------- --------------------------------------------
  **Requirement   **Priority**   **Description**
  ID**                           

  H8-03-A         HIGH           Discover result cards must use the same
                                 reusable card component as AI Stylist result
                                 cards. The \'+ Add to Wardrobe\' button
                                 (H8-01-A/B/C/D) is inherited automatically.

  H8-03-B         MEDIUM         When items are added from Discover, they
                                 appear in My Wardrobe with a visual
                                 tag/chip: \'From Discover\' (light blue) vs
                                 items added from AI Stylist which show
                                 \'From Stylist\' (light gold). This helps
                                 the user remember the source context.

  H8-03-C         LOW            The Wardrobe tab badge count (e.g. \'✦ AI
                                 WARDROBE (3)\') must update in real-time
                                 when items are added from Discover, without
                                 requiring a tab switch.
  --------------- -------------- --------------------------------------------

**Change 4 --- Try It On: Category Picker & Outfit Composition**

**Problem**

The current Try It On flow shows the complete wardrobe and composites
all items onto the model at once. This is not useful when a user has
multiple items of the same category (e.g. two tops). There is no way to
select which specific combination to try.

**Solution**

Redesign the Try It On interface into a two-step flow: (1)
category-based item picker, then (2) model image generation with the
selected combination.

**Step 1 --- Category Picker**

Group all wardrobe items by their articleType/category. For each
category, display the items as small thumbnail chips. The user selects
ONE item per category to compose the final outfit.

> ┌──────────────────────────────────────────────┐
>
> │ Build Your Outfit │
>
> ├──────────────────────────────────────────────┤
>
> │ TOPS (pick one) │
>
> │ \[img A\] \[img B ✓\] \[img C\] │
>
> ├──────────────────────────────────────────────┤
>
> │ BOTTOMS (pick one) │
>
> │ \[img D ✓\] │
>
> ├──────────────────────────────────────────────┤
>
> │ FOOTWEAR (pick one) │
>
> │ \[img E ✓\] \[img F\] │
>
> ├──────────────────────────────────────────────┤
>
> │ \[→ Try This Outfit\] │
>
> └──────────────────────────────────────────────┘

**Step 2 --- Model Generation**

Once the user confirms the selection, generate the composite model image
using only the selected items (same CSS composite approach as before,
but filtered to one item per category).

  --------------- -------------- --------------------------------------------
  **Requirement   **Priority**   **Description**
  ID**                           

  H8-04-A         HIGH           In Try It On, group wardrobe items by
                                 category (articleType). Display each
                                 category as a horizontal row with a \'pick
                                 one\' instruction. Each item is shown as a
                                 small square thumbnail (80×80px).

  H8-04-B         HIGH           Item selection is single-select per category
                                 row. Selecting an item highlights it with a
                                 gold border and a ✓ overlay. Clicking a
                                 selected item deselects it (no item selected
                                 for that category is valid).

  H8-04-C         HIGH           A \'Try This Outfit\' CTA button is shown
                                 below all category rows. It is disabled
                                 (greyed) if zero items are selected. It
                                 activates as soon as at least one item is
                                 selected.

  H8-04-D         HIGH           On click of \'Try This Outfit\', pass only
                                 the selected items (one per category) to the
                                 composite generation logic. The model image
                                 is generated using only those items layered
                                 in z-order: footwear → bottoms → tops →
                                 outerwear.

  H8-04-E         MEDIUM         Show a loading state on the model preview
                                 area while the composite is being prepared
                                 (\'Putting your outfit together...\').
                                 Estimated time: \<2s for CSS composite.

  H8-04-F         LOW            Allow the user to go back to the picker and
                                 change their selection without losing
                                 previous choices. The picker remembers the
                                 last selection state during the session.
  --------------- -------------- --------------------------------------------

**Change 5 --- AI Stylist Companion (New Feature)**

**Concept**

After the user composes an outfit in Try It On, an AI Stylist Companion
evaluates the combination against the user\'s stated occasion/event. It
provides a score and actionable advice --- helping the user decide if
this outfit is optimal or if a different combination would work better.

**User Journey**

1\. User finishes selecting items in Try It On category picker.

2\. Below the model preview, a \'Get Style Advice\' button appears.

3\. On click, the system calls GPT-4o-mini with: all selected item
descriptions + the occasion text the user typed in Discover.

4\. The model returns a structured JSON with: overall_score (0--10),
per_item scores, verdict text, and improvement suggestion.

5\. The result is displayed as an elegant \'Companion Panel\' below the
model preview.

**Companion Panel Layout**

> ┌──────────────────────────────────────────────┐
>
> │ ✦ AI Stylist Companion │
>
> ├──────────────────────────────────────────────┤
>
> │ Occasion: \'Casual dinner, summer evening\' │
>
> │ │
>
> │ Overall Score: 7.4 / 10 ████████░░ │
>
> │ │
>
> │ Item Breakdown: │
>
> │ • White Linen Shirt 9/10 ✓ │
>
> │ • Navy Chinos 8/10 ✓ │
>
> │ • Brown Chelsea Boots 5/10 ⚠ │
>
> │ │
>
> │ Verdict: \'Strong casual look. The boots │
>
> │ are slightly heavy for a summer dinner. │
>
> │ Consider swapping for loafers or sandals.\' │
>
> │ │
>
> │ \[↻ Try a different combination\] │
>
> └──────────────────────────────────────────────┘

**GPT-4o-mini Prompt (backend --- new endpoint)**

Create a new backend endpoint: POST /api/companion-evaluate

Request body:

> { \"occasion\": \"string\", \"items\": \[{ \"name\": \"string\",
> \"category\": \"string\", \"description\": \"string\" }\] }

System prompt to GPT-4o-mini:

> *You are an expert fashion stylist. You will receive a list of
> clothing items and the occasion the user is dressing for. Evaluate how
> well the outfit works for that occasion. Return ONLY a JSON object
> with no markdown. Schema: { \"overall_score\": float (0-10),
> \"items\": \[{ \"name\": string, \"score\": float, \"comment\": string
> }\], \"verdict\": string (2-3 sentences), \"improvement\": string (1
> actionable suggestion) }*

  --------------- -------------- --------------------------------------------
  **Requirement   **Priority**   **Description**
  ID**                           

  H8-05-A         HIGH           Create POST /api/companion-evaluate
                                 endpoint. Accepts: { occasion: string,
                                 items: \[{name, category, description}\] }.
                                 Returns the GPT-4o-mini JSON response parsed
                                 and validated.

  H8-05-B         HIGH           In the Try It On view, after a combination
                                 is selected, show a \'Get Style Advice ✦\'
                                 button below the model preview. This button
                                 is only visible after at least one item is
                                 selected.

  H8-05-C         HIGH           On API response, render the Companion Panel
                                 with: overall score as a numeric + progress
                                 bar (0--10 scale), per-item scores as a list
                                 with ✓ (≥7) or ⚠ (\<7) indicators, verdict
                                 text, and improvement suggestion.

  H8-05-D         HIGH           The occasion text passed to the companion
                                 must be the same text the user typed in the
                                 Discover tab\'s occasion input. It must be
                                 stored in frontend state and passed through
                                 to Try It On. If no occasion was typed (user
                                 added items via Stylist only), show an input
                                 field in the Companion Panel to collect it
                                 before evaluation.

  H8-05-E         MEDIUM         Score colour coding: overall score ≥8 →
                                 green; 6--7.9 → amber; \<6 → red. Per-item
                                 score ≥7 → ✓ green; \<7 → ⚠ amber.

  H8-05-F         MEDIUM         Loading state while the API call is in
                                 progress: show a pulsing \'✦ Your AI Stylist
                                 is reviewing your outfit...\' message in the
                                 panel area. Estimated latency: 2--4s.

  H8-05-G         LOW            \'Try a different combination\' button
                                 resets the Try It On picker to Step 1
                                 (category selector), clearing the companion
                                 evaluation result. The wardrobe items remain
                                 unchanged.

  H8-05-H         LOW            Log the companion evaluation call in the
                                 existing analytics/logging system
                                 (request_id, occasion length, item count,
                                 overall_score returned, latency_ms).
  --------------- -------------- --------------------------------------------

**Implementation Order & Dependencies**

Claude Code must implement changes in the following order to avoid
integration issues:

  ---------- ---------------- ----------------------- ---------------------
  **Step**   **Change**       **What to build**       **Depends on**

  1          Change 1         Shared card component   None --- start here
                              with repositioned Add   
                              button + toggle state   

  2          Change 3         Discover uses same card Step 1
                              component (mostly free  
                              if step 1 is clean)     

  3          Change 2         Wardrobe management UI  Step 1 (card
                              (clear all, manage      component)
                              mode, × per card)       

  4          Change 4         Try It On category      Step 3 (wardrobe
                              picker + filtered       state)
                              composite generation    

  5          Change 5         AI Companion endpoint + Step 4 (picker
                              panel UI                selection state +
                                                      occasion string)
  ---------- ---------------- ----------------------- ---------------------

**Acceptance Criteria (Definition of Done)**

Each requirement above is DONE when:

- The stated UI element renders correctly on desktop (1280px) and mobile
  (390px)

- The action completes without console errors

- Edge cases are handled: empty wardrobe, no occasion text, API error
  from companion

- The GPT-4o-mini companion call returns a valid parseable JSON --- if
  malformed, show a friendly error: \'Style advice unavailable. Try
  again.\'

- All new API endpoints follow existing FastAPI patterns (async, proper
  error codes, logged)

- No existing AI Stylist or Discover functionality is broken by these
  changes

*GPToutfit · Handoff 8 · v1.0 · Product Owner: Javier Lombana ·
Confidential*
