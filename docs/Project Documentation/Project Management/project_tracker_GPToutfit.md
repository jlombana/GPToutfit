**GPToutfit**

Project Management Document

*Version 4.0 · March 7, 2026 · AI Wardrobe + 6-Sprint Roadmap*

**Version History**

  --------- ------------ ------------- ---------------------------------------------
    **v**     **Date**    **Author**                    **Summary**

   **1.0**   2026-03-01   Engineering          Initial plan, Sprint 0 closed

   **2.0**   2026-03-06  Product Owner    RetailNext pivot, Sprint 1--4 planned,
                                                       Handoffs 1--4

   **3.0**   2026-03-07  Product Owner Catalog diagnosis, Sprint 2 URGENT, Handoffs
                                                5--6, risk register updated

   **4.0**   2026-03-07  Product Owner AI Wardrobe tab: occasion discovery + try-on
                                           live inside AI Wardrobe. Sprints 4--5
                                                defined. 8-task Handoff 7.
  --------- ------------ ------------- ---------------------------------------------

**1. Project Status**

- Sprint 2 --- IN PROGRESS / URGENT: catalog expansion to 10K from local
  Kaggle dataset + adaptive thresholds + enriched embeddings. Blocks AI
  Wardrobe quality.

- Sprint 3 --- Planned: product images, outfit board, graceful error
  states, unit tests, Docker.

- Sprint 4 --- Planned: AI Wardrobe Core (nav badge, checkboxes in AI
  Stylist, profile modal, Discover UI + backend).

- Sprint 5 --- Planned: AI Wardrobe Try-On (Discover grid, My Wardrobe
  board, composite try-on).

- Sprint 6 --- Planned: RetailNext demo prep --- B2B features, load
  testing, cloud deployment.

**2. Sprint Plan**

  ------------ ----------- ---------------- ------------ ----------------------------------------
   **Sprint**   **Dates**     **Theme**      **Status**            **Key Deliverables**

  **Sprint 0** Feb 20--Mar  **Foundation**   **Complete       FR-01--14, core RAG pipeline,
                    1                           ✅**       GPT-4o-mini vision, cosine matching

  **Sprint 1** Mar 2--Mar   **UI & Modes**   **Complete     Occasion input, dual search modes
                    6                           ✅**       (Complete My Outfit / Find Similar),
                                                          RetailNext branding, editorial voice,
                                                                      associate mode

  **Sprint 2** Mar 7--Mar   **Catalog Fix       **In     Handoff 5: adaptive thresholds, enriched
                   14        --- URGENT**     Progress   embeddings, fallback expansion. Handoff
                                                🔄**     6: expand_catalog.py --- 10K stratified
                                                             sample from local Kaggle dataset
                                                          (sample_images_large/fashion-dataset/)

  **Sprint 3** Mar 15--Mar **Quality & Core  **Planned      FR-15 product images, FR-16 outfit
                   21            UX**           📋**     board, FR-18 graceful no-match, FR-17 UI
                                                             polish, unit tests ≥80%, Docker
                                                                     containerisation

  **Sprint 4** Mar 22--Mar  **AI Wardrobe    **Planned     H7-01 nav badge, H7-02 checkboxes AI
                   28           Core**          📋**        Stylist, H7-03 AI Wardrobe page +
                                                          profile modal, H7-04 Discover section
                                                           UI, H7-05 backend /wardrobe/discover

  **Sprint 5** Mar 29--Apr  **AI Wardrobe    **Planned    H7-06 Discover results grid, H7-07 My
                    4          Try-On**         📋**     Wardrobe board, H7-08 Try It On section
                                                         (option modal + composite render + deep
                                                                          link)

  **Sprint 6** Apr 5--Apr    **RetailNext    **Planned    FR-25--34 B2B features, load testing,
                   11        Demo Prep**        📋**          cloud deployment, pitch deck,
                                                               stakeholder demo run-through
  ------------ ----------- ---------------- ------------ ----------------------------------------

**3. AI Wardrobe Feature Tracker**

All AI Wardrobe features depend on Sprint 2 completing first. The
occasion discovery endpoint (FR-35) produces poor results with only 1K
catalog items.

  -------------- -------- ------------ ------------ ----------- -------------- -------------------------------
   **Feature**    **BR**     **FR**     **Sprint**   **Tasks**   **Priority**             **Notes**

  **AI WARDROBE   BR-22    **FR-41**     Sprint 4      H7-01       **Must**    Entry point to the new section.
    nav link +                                                                 Badge reflects shared basket in
   live badge**                                                                          real-time.

   **Checkboxes   BR-21    **FR-36a**    Sprint 4      H7-02       **Must**    Shared basket with AI Wardrobe.
  on AI Stylist                                                                         Max 20 items.
     cards**                                                                   

    **Gender &    BR-23    **FR-40**     Sprint 4      H7-03       **Must**      One-time modal on first AI
  style profile                                                                Wardrobe visit. Drives discover
     modal**                                                                     relevance + try-on gender.

    **Discover    BR-24    **FR-35**     Sprint 4     H7-04,       **Must**    Requires catalog ≥10K (Handoff
   section ---                                         H7-05                       6 prerequisite). Reuses
     occasion                                                                     existing embedding infra.
    textarea**                                                                 

    **Discover    BR-25    **FR-36b**    Sprint 5      H7-06       **Must**       Same shared basket as AI
  results grid +                                                                 Stylist. Category grouping.
   checkboxes**                                                                

  **My Wardrobe   BR-26    **FR-37**     Sprint 5      H7-07       **Must**      Grouped by category. Price
     board**                                                                     total. Shop All + Try It On
                                                                                            CTAs.

   **Try It On    BR-27    **FR-38**     Sprint 5      H7-08       **Must**        Model SVG or user photo
    --- option                                                                     (client-side only). CSS
     modal +                                                                      overlay. Privacy notice.
   composite**                                                                 

   **Try It On    BR-28    **FR-39**    Sprint 7+       TBD       **Could**     Replicate IDM-VTON. Separate
      --- AI                                                                       budget approval needed.
    Generative                                                                 
   (Phase 4)**                                                                 
  -------------- -------- ------------ ------------ ----------- -------------- -------------------------------

**4. Key Architectural Decision --- v4.0**

**Occasion Discovery lives in AI Wardrobe, not AI Stylist**

In v4.0 the occasion textarea (Discover) and the virtual try-on (Try It
On) both live inside the AI Wardrobe tab. This keeps AI Stylist clean
and focused on item-first discovery, while AI Wardrobe serves as the
creative, occasion-first destination.

The basket is the bridge: items saved from AI Stylist (via checkboxes on
result cards) appear inside AI Wardrobe My Wardrobe. Items saved from AI
Wardrobe Discover also go into the same basket. The user moves naturally
between both sections without losing context.

**5. Handoff Summary --- All Handoffs**

**Handoffs 1--4 (Sprint 1 --- Complete ✅)**

- H1: Occasion input, match quality labels, associate mode, inventory
  badge, editorial voice

- H2: Embedding enrichment --- build_rich_description(), USAGE_SYNONYMS
  dict

- H3: Dual search mode UI (Complete My Outfit / Find Similar Items)

- H4: RetailNext branding --- promo bar, full nav, footer

**Handoff 5 --- Catalog Quality Fix (Sprint 2 --- In Progress 🔄)**

- Adaptive cosine thresholds (COMPLEMENTARY=0.30 / SIMILARITY=0.50),
  3-tier fallback expansion, vocabulary alignment, startup validation
  (min 5K items check)

**Handoff 6 --- Catalog Expansion Script (Sprint 2 --- In Progress 🔄)**

- scripts/expand_catalog.py: reads
  sample_clothes/sample_images_large/fashion-dataset/styles.csv, takes
  random stratified sample of 10K rows, copies images to sample_images/,
  deletes embeddings cache

**Handoff 7 --- AI Wardrobe Tab (Sprints 4--5 --- Planned 📋)**

- H7-01: ✦ AI WARDROBE nav link + live basket counter badge

- H7-02: Save-to-Wardrobe checkboxes on all AI Stylist result cards

- H7-03: AI Wardrobe page shell + gender & style profile modal
  (first-visit only)

- H7-04: ① Discover section --- occasion textarea + \'Find My Outfit\'
  button

- H7-05: Backend POST /wardrobe/discover endpoint

- H7-06: ① Discover results grid with checkboxes + category grouping

- H7-07: ② My Wardrobe board --- grouped items, price total, Shop All +
  Try It On CTAs

- H7-08: ③ Try It On --- option modal (AI Model vs own photo) + CSS
  composite render + deep link from My Wardrobe

**6. Dependencies & Critical Path**

Handoff 6 (catalog 10K) must complete before Sprint 4 begins (AI
Wardrobe discover quality depends on it)

Handoff 5 (adaptive thresholds) can run in parallel with Handoff 6 ---
same sprint

H7-01 (nav badge) + H7-02 (checkboxes) can run in parallel --- no
dependency between them

H7-03 (page shell + modal) must complete before H7-04 (Discover UI needs
the page to exist)

H7-05 (backend endpoint) must complete before H7-06 (frontend grid calls
the endpoint)

H7-07 (My Wardrobe board) must complete before H7-08 (Try It On deep
link targets it)

Model assets (model_male.png, model_female.png) must be ready before
H7-08

*GPToutfit · Project Management · v4.0 · Confidential*
