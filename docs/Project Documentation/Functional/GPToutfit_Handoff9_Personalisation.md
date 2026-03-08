**GPToutfit**

**Handoff 9 --- Personalisation, Smart Outfit Logic & Discovery**

*For Claude Code · v1.0 · March 2026*

**Overview & Scope**

This handoff covers 4 interconnected enhancements that together move
GPToutfit from a recommendation tool to a personalised AI styling
experience. The changes introduce user profiles, context-aware outfit
completeness logic, a keyword search mode, and a progressive onboarding
survey.

These 4 changes must be implemented in the order defined in Section 6
(Implementation Order), as each layer depends on the one before it. The
profile system (Change 3) is foundational --- it must be in place before
Changes 1 and 4 can use it.

**Change 1 --- Context-Aware Outfit Completeness**

**Problem**

Currently, a user can end up in Try It On with only one or two items ---
e.g. just a shirt --- even when the occasion clearly demands a full
outfit. The AI Companion then has nothing meaningful to evaluate. The
system needs to understand what a \'complete outfit\' means for a given
context and actively guide the user towards it.

**Solution**

When the user submits an occasion in Discover (or via the profile
survey), the backend derives a required outfit template based on context
--- formality level, season, gender --- and shows the user which
categories are still missing from their wardrobe. The user is never
blocked, but clearly guided.

**Outfit Template Logic**

The backend must classify the occasion into one of 4 formality tiers,
then map each tier to a minimum required category set:

  ------------- ---------------- ------------------------------------
  **Tier**      **Examples**     **Minimum Required Categories**

  Formal        Job interview,   Top (shirt/blouse) + Bottom
                gala, keynote    (trousers/skirt) + Outerwear
                                 (jacket/blazer) + Footwear +
                                 Accessory (optional)

  Smart Casual  Client dinner,   Top + Bottom + Footwear + Outerwear
                gallery opening, (optional)
                first date at    
                wine bar         

  Casual        Weekend brunch,  Top + Bottom + Footwear
                city walk,       
                coffee with      
                friends          

  Active /      Beach, gym,      Top + Bottom or Swimwear + Footwear
  Resort        hiking, pool     (optional)
                party            
  ------------- ---------------- ------------------------------------

> *Formality tier classification is done via a single GPT-4o-mini call
> on the occasion text. Prompt: \'Classify this occasion into one of
> \[Formal, Smart Casual, Casual, Active/Resort\]. Return only the tier
> name.\' Cache the result in frontend state alongside the occasion
> string.*

**UI: Outfit Completeness Bar**

In the My Wardrobe tab, show a visual completeness indicator above the
item grid:

> ┌─────────────────────────────────────────────────────┐
>
> │ Your outfit for: \'Job interview at a tech startup\' │
>
> │ Formality: Formal │
>
> │ │
>
> │ ✓ Top (shirt) ✓ Bottom (trousers) │
>
> │ ✓ Outerwear ✗ Footwear ✗ Accessory │
>
> │ │
>
> │ Progress: ████████░░ 3/5 categories │
>
> │ \[+ Find Missing Items →\] (links back to Stylist) │
>
> └─────────────────────────────────────────────────────┘

  ------------- -------------- ----------------------------------------------
  **ID**        **Priority**   **Requirement**

  H9-01-A       HIGH           On occasion submission in Discover, make a
                               GPT-4o-mini call to classify the formality
                               tier. Store tier + required categories in
                               frontend session state alongside the occasion
                               text.

  H9-01-B       HIGH           In My Wardrobe tab, render an \'Outfit
                               Completeness\' card above the item grid. It
                               shows: occasion summary, formality tier,
                               required categories with ✓/✗ status based on
                               current wardrobe contents.

  H9-01-C       HIGH           A \'+ Find Missing Items\' CTA links to AI
                               Stylist with the missing category pre-filled
                               as search context (e.g. if Footwear is
                               missing, AI Stylist opens with a prompt
                               pre-loaded: \'Find footwear that matches
                               \[occasion\]\').

  H9-01-D       MEDIUM         The AI Companion (Handoff 8, Change 5) must
                               receive the formality tier alongside the
                               occasion and item list. Add tier to the
                               companion prompt: \'The occasion is Formal.
                               Evaluate accordingly.\'

  H9-01-E       MEDIUM         If the user enters Try It On with fewer than
                               the minimum required categories filled, show a
                               soft warning banner: \'Your outfit may feel
                               incomplete. Consider adding \[missing
                               categories\] for a more polished look.\' The
                               user can dismiss and continue.

  H9-01-F       LOW            The completeness bar progress updates in
                               real-time as items are added or removed from
                               the wardrobe, without requiring a page/tab
                               refresh.
  ------------- -------------- ----------------------------------------------

**Change 2 --- AI Stylist: \'I Know What I Want\' Keyword Search**

**Context**

AI Stylist currently has two modes: \'Complete My Outfit\' (image
upload) and \'Find Similar Items\'. This change adds a third mode for
users who want to search the catalog directly by keyword or natural
language description --- no image required. This gives power users a
faster path and increases catalog discoverability.

**Mode Design**

The three modes in AI Stylist tab navigation:

> \[ 📷 Complete My Outfit \] \[ 🔍 Find Similar Items \] \[ ✏️ I Know
> What I Want \]

The new third mode presents a single text input and a search button. No
image upload required.

**Search Behaviour**

The keyword search does NOT call GPT-4o-mini for analysis. It goes
directly to the RAG embedding search layer --- the user\'s text is
embedded and matched against the catalog. This keeps latency under 2
seconds and avoids unnecessary AI cost for simple lookups.

> *This is intentionally a lightweight path. The value of AI analysis is
> reserved for the image-based flows. Keyword search is about speed and
> control for users who already know what they want.*

  ------------- -------------- ----------------------------------------------
  **ID**        **Priority**   **Requirement**

  H9-02-A       HIGH           Add a third tab/mode to AI Stylist: \'I Know
                               What I Want\' (icon: ✏️ or search icon). It
                               renders a text input field with placeholder:
                               \'e.g. grey linen trousers, white summer
                               dress, black leather loafers\...\'

  H9-02-B       HIGH           On submit, embed the user\'s text using the
                               existing embeddings module and run cosine
                               similarity search against the full catalog.
                               Return top 6 results (threshold: 0.5, top_k:
                               6). Do NOT call GPT-4o-mini for this flow.

  H9-02-C       HIGH           Results are displayed using the same shared
                               card component (Handoff 8, Change 1) with the
                               \'+ Add to Wardrobe\' button. Items added from
                               this mode show a \'From Search\' chip tag in
                               the wardrobe.

  H9-02-D       MEDIUM         Allow multiple searches in sequence without
                               clearing previous results --- append new
                               results below, with a divider and the search
                               term as a section header. This lets users
                               build up a shortlist from multiple queries.

  H9-02-E       MEDIUM         Add a gender filter toggle above the results
                               (Men / Women / Unisex) pre-populated from the
                               active user profile (Change 3). The user can
                               override it.

  H9-02-F       LOW            Show a result count: \'Found 6 items matching
                               \"grey linen trousers\"\'. If 0 results, show:
                               \'No exact matches. Try broader terms or use
                               Complete My Outfit for AI-powered
                               suggestions.\'
  ------------- -------------- ----------------------------------------------

**Change 3 --- User Profiles: Javier & Laura (Demo)**

**Purpose**

User profiles are the foundation of personalisation. Without them,
recommendations are generic. With them, the system can pre-filter by
gender, size, and style preference --- and the AI Companion can evaluate
outfits in the context of a real person\'s body, budget, and taste.

For the demo, two complete profiles are hardcoded in the frontend. A
profile selector appears at the top of the AI Wardrobe section.
Switching profiles resets the current wardrobe session.

**Profile Selector UI**

> ┌──────────────────────────────────────────────┐
>
> │ 👤 Active Profile: \[ Javier ▾ \] \[ Laura \] │
>
> │ Height: 185cm · Size: XL · Style: Smart │
>
> └──────────────────────────────────────────────┘

**Profile: Javier Lombana**

  ----------------------- ------------------------------------------
  Full Name               Javier Lombana

  Age                     38

  Location                Madrid, Spain

  Gender                  Male

  Height                  185 cm

  Weight                  100 kg

  Build                   Athletic / Broad shoulders

  Top Size                XL (EU 54)

  Trouser Size            W36 L32

  Shoe Size               44 EU / 10 UK

  Jacket Size             XL / EU 54

  Preferred Style         Smart casual, business casual, minimal. No
                          streetwear or loud prints.

  Favourite Brands        Massimo Dutti, Zara Man, Hugo Boss, Calvin
                          Klein, Tommy Hilfiger

  Budget per item         €50--€200. Occasional splurge to €350 for
                          outerwear or shoes.

  Colours                 Navy, charcoal, white, camel, olive green.
                          Avoids bright colours.

  Fit preference          Slim-fit shirts, straight or slim
                          trousers. Not skinny.

  Typical occasions       Business meetings, client dinners, weekend
                          city walks, travel

  Dislikes                Synthetic fabrics, visible logos, overly
                          casual looks in professional settings
  ----------------------- ------------------------------------------

**Javier --- Simulated Purchase History**

  ----------------------- ------------- ------------- ----------------
  **Item**                **Brand**     **Price**     **Season**

  Navy slim-fit blazer    Massimo Dutti €189          AW 2024

  White Oxford shirt      Zara Man      €39           SS 2024

  Charcoal slim chinos    Hugo Boss     €119          AW 2024

  White linen shirt       Massimo Dutti €79           SS 2024

  Brown leather Chelsea   Zara Man      €89           AW 2023
  boots                                               

  Navy crewneck sweater   Calvin Klein  €89           AW 2024

  Beige trench coat       Tommy         €299          AW 2023
                          Hilfiger                    

  Grey merino polo        Massimo Dutti €69           SS 2025

  Black leather belt      Hugo Boss     €55           AW 2024

  White trainers          Calvin Klein  €95           SS 2024
  ----------------------- ------------- ------------- ----------------

**Profile: Laura García**

  ----------------------- ------------------------------------------
  Full Name               Laura García

  Age                     31

  Location                Barcelona, Spain

  Gender                  Female

  Height                  167 cm

  Weight                  58 kg

  Build                   Slim / Pear shape

  Top Size                S (EU 36)

  Trouser/Skirt Size      S / EU 36, Waist 27

  Shoe Size               38 EU / 5 UK

  Dress Size              EU 36 / UK 8

  Preferred Style         Feminine minimal, effortless chic. Mix of
                          classic pieces with modern cuts.

  Favourite Brands        & Other Stories, Mango, Cos, Arket, Sandro

  Budget per item         €30--€150. Up to €250 for coats or special
                          occasion dresses.

  Colours                 Ivory, blush, terracotta, sage green,
                          black. Avoids neons and dark navy.

  Fit preference          Fitted tops, wide-leg or straight
                          trousers, midi lengths. Avoids bodycon.

  Typical occasions       Creative agency work, rooftop drinks,
                          weekend markets, travel, gallery events

  Dislikes                Fast fashion basics, overly sporty looks,
                          very structured corporate style
  ----------------------- ------------------------------------------

**Laura --- Simulated Purchase History**

  ----------------------- ------------- ------------- ----------------
  **Item**                **Brand**     **Price**     **Season**

  Ivory silk blouse       & Other       €79           SS 2024
                          Stories                     

  Terracotta wide-leg     Mango         €59           SS 2024
  trousers                                            

  Camel wool coat         Arket         €229          AW 2024

  Black midi wrap dress   Cos           €99           AW 2024

  Sage green linen shirt  & Other       €69           SS 2025
                          Stories                     

  White straight-leg      Mango         €49           SS 2024
  jeans                                               

  Blush knit cardigan     Arket         €89           AW 2024

  Brown suede ankle boots & Other       €149          AW 2023
                          Stories                     

  Gold hoop earrings set  Sandro        €65           SS 2024

  Beige linen blazer      Cos           €119          SS 2025
  ----------------------- ------------- ------------- ----------------

**Profile System --- Technical Requirements**

  ------------- -------------- ----------------------------------------------
  **ID**        **Priority**   **Requirement**

  H9-03-A       HIGH           Profiles are stored as a hardcoded JSON object
                               in the frontend (profiles.js or equivalent).
                               Each profile contains: id, name, gender,
                               height, weight, build, sizes (top, bottom,
                               shoe, dress/jacket), style_tags\[\],
                               preferred_brands\[\], budget_range,
                               preferred_colours\[\], dislikes\[\],
                               purchase_history\[\].

  H9-03-B       HIGH           A profile selector UI is shown at the top of
                               the AI Wardrobe section. Switching profiles
                               shows a confirmation: \'Switch to \[Name\]?
                               Your current wardrobe session will be
                               cleared.\' The active profile name and 3 key
                               stats (height, top size, style) are displayed
                               in a compact header strip.

  H9-03-C       HIGH           The active profile\'s gender filters ALL
                               catalog queries automatically: Discover
                               results, AI Stylist results, and keyword
                               search (Change 2) are pre-filtered by profile
                               gender. The user can override the filter
                               manually.

  H9-03-D       HIGH           The active profile is passed to the AI
                               Companion endpoint (Handoff 8, Change 5) in
                               every evaluation call. The companion prompt
                               must include: name, height, weight, build,
                               preferred style, and occasion. This enables
                               body-aware and taste-aware scoring.

  H9-03-E       MEDIUM         The AI Companion prompt addendum for profiles:
                               \'You are evaluating an outfit for \[Name\],
                               \[height\], \[build\]. Their preferred style
                               is \[style_tags\]. They dislike \[dislikes\].
                               Score the outfit considering fit for their
                               build and alignment with their taste.\'

  H9-03-F       MEDIUM         Purchase history is used to enrich the
                               Discover recommendations prompt: include the
                               last 3 purchased items in the GPT-4o-mini
                               Discover call as context: \'The user recently
                               purchased: \[item1\], \[item2\], \[item3\].
                               Suggest items that complement their existing
                               wardrobe.\'

  H9-03-G       LOW            Display a \'Style DNA\' chip row under the
                               profile selector showing the profile\'s
                               style_tags as visual chips (e.g. \'Smart
                               Casual\', \'Minimal\', \'Natural Colours\').
                               These are decorative in v1 but will feed
                               filtering logic in v2.
  ------------- -------------- ----------------------------------------------

**Change 4 --- Progressive Onboarding Survey**

**Design Philosophy**

A traditional survey before the experience kills engagement. Instead,
GPToutfit uses a progressive model: collect the minimum needed to start
(2 questions), then gather richer data at natural pause points in the
journey. The survey never feels like a form --- it feels like the app
getting to know you.

> *PO recommendation: Maximum 2 questions at entry. Additional questions
> surface inline, triggered by context --- never as a blocking step.
> Every question must feel like it directly improves the next result the
> user sees.*

**Survey Flow --- 3 Stages**

**Stage 1: Entry (shown once, first visit only --- before Discover)**

2 questions presented as visual chip selectors, not text inputs:

> Q1: \'What best describes your style?\' (single select)
>
> \[ Minimal & Clean \] \[ Smart & Polished \] \[ Casual & Relaxed \] \[
> Bold & Expressive \]
>
> Q2: \'What\'s your typical budget per item?\'
>
> \[ Under €50 \] \[ €50--€100 \] \[ €100--€200 \] \[ €200+ \]

Both answers are stored in profile state and used immediately to filter
Discover results and bias the AI Companion scoring.

**Stage 2: Contextual (inline, triggered during the session)**

These questions appear as soft prompts inside the flow --- not blocking
modals:

> Trigger: User adds 3+ items from the same category
>
> → Soft prompt above results: \'You seem to love \[category\]. Do you
> prefer \[Fitted\] or \[Relaxed\] cuts?\'
>
> Trigger: User\'s occasion is classified as Formal
>
> → \'For formal occasions, do you prefer: \[Classic & Traditional\] or
> \[Modern & Architectural\]?\'
>
> Trigger: User views Try It On for the first time
>
> → \'Would you like recommendations to include: \[Accessories &
> Jewellery\]? \[Yes\] \[Not now\]\'

**Stage 3: Post Try-On Feedback (optional, after companion evaluation)**

After the AI Companion scores the outfit, a single optional question:

> \'Was this advice helpful?\' \[Very helpful ★★★\] \[Somewhat ★★\]
> \[Not really ★\]
>
> → If \'Not really\': \'What would you like more of?\'
>
> \[ More formal options \] \[ Lower price range \] \[ Different colours
> \] \[ Different brands \]

  ------------- -------------- ----------------------------------------------
  **ID**        **Priority**   **Requirement**

  H9-04-A       HIGH           Stage 1 survey renders as a modal overlay on
                               first visit to AI Wardrobe (before the
                               Discover tab loads). It shows Q1 (style
                               preference) and Q2 (budget) as visual chip
                               selectors. A \'Skip for now\' link is always
                               visible. Answers are saved to profile state.

  H9-04-B       HIGH           If an active profile is selected (Change 3,
                               Javier or Laura), the Stage 1 survey is
                               SKIPPED --- the profile already contains this
                               information. The survey only appears for a
                               \'guest\' or new user state.

  H9-04-C       HIGH           Stage 1 answers (style + budget) are used
                               immediately: budget filters out catalog items
                               above the stated range; style tag biases the
                               Discover prompt (\'The user prefers \[Minimal
                               & Clean\] style\').

  H9-04-D       MEDIUM         Stage 2 contextual prompts appear as a slim
                               banner at the top of the results area (not a
                               modal). They are dismissable with an × and
                               never repeat after dismissal. Answers update
                               profile state silently.

  H9-04-E       MEDIUM         Stage 3 feedback renders below the AI
                               Companion panel after evaluation. It is
                               optional and non-blocking. Responses are
                               logged to the analytics system (alongside
                               companion score data from H8-05-H).

  H9-04-F       LOW            A \'My Preferences\' link in the profile strip
                               (Change 3 header) opens a side panel showing
                               all collected survey answers with the option
                               to edit them. Changes take effect on the next
                               search or Discover request.
  ------------- -------------- ----------------------------------------------

**Implementation Order & Dependencies**

CRITICAL: Change 3 (Profiles) must be implemented first. All other
changes depend on the profile system being in place.

  ---------- -------------- --------------------------- ---------------------
  **Step**   **Change**     **What to build**           **Depends on**

  1          Change 3 ---   Profile JSON, selector UI,  None --- START HERE
             Profiles       gender filter propagation,  
                            profile → companion         
                            integration                 

  2          Change 4 ---   Entry survey modal for      Step 1 (profile state
             Survey (Stage  guest users. Skip logic for must exist)
             1 only)        profile users. Budget +     
                            style filters.              

  3          Change 2 ---   Third AI Stylist mode.      Step 1 (gender
             Keyword Search Embedding search. Results   pre-filter from
                            with shared card component. profile)

  4          Change 1 ---   Formality classification    Step 1 (profile
             Outfit         call. Completeness bar UI.  gender + style), Step
             Completeness   \'Find Missing Items\' CTA. 3 (keyword search is
                                                        the landing for
                                                        \'Find Missing
                                                        Items\')

  5          Change 4 ---   Contextual inline prompts.  Step 4 (companion
             Survey (Stages Post-companion feedback     must be live, outfit
             2 & 3)         widget.                     flow must be
                                                        complete)
  ---------- -------------- --------------------------- ---------------------

**Data Flow --- How Profile Enriches Every API Call**

The diagram below shows how profile data flows through all active
systems after Handoff 9 is implemented:

> User selects profile (Javier / Laura)
>
> │
>
> ├─► Gender filter → all catalog queries (Discover, Stylist, Search)
>
> ├─► Size data → (future: filter by available sizes)
>
> ├─► Style tags → Discover GPT prompt enrichment
>
> ├─► Budget range → filter out items above budget
>
> ├─► Purchase history (last 3) → Discover prompt context
>
> └─► Full profile object → AI Companion evaluation prompt
>
> Occasion text (from Discover or survey)
>
> │
>
> ├─► Formality tier classification (GPT call, cached)
>
> ├─► Required outfit categories → Completeness bar
>
> └─► AI Companion context

**Acceptance Criteria (Definition of Done)**

- Profile switch correctly resets wardrobe session and updates all
  active filters

- Discover results for Javier only show Male/Unisex items; for Laura
  only Female/Unisex

- Keyword search returns results in under 2 seconds with no GPT-4o-mini
  call in the path

- Completeness bar reflects live wardrobe state --- updates without page
  refresh

- AI Companion prompt includes profile name, build, and style tags in
  every call

- Stage 1 survey appears for guest users, is skipped for Javier/Laura
  profiles

- \'Find Missing Items\' CTA correctly pre-loads the missing category
  into AI Stylist keyword search

- No existing flows (AI Stylist image upload, guardrail, Try It On
  composite) are broken

*GPToutfit · Handoff 9 · v1.0 · Product Owner: Javier Lombana ·
Confidential*
