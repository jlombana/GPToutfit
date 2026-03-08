**GPToutfit**

Functional Requirements Document

Version 5.0 · March 8, 2026 · AI Wardrobe + Generative Try-On

**Version History**

  --------- ------------ --------------- ------------------------------
  **v**     **Date**     **Author**      **Summary**

  1.0       2026-03-01   Engineering     Initial MVP --- FR-01--14,
                                         core RAG pipeline

  2.0       2026-03-06   Product Owner   Phase 2--4 roadmap, FR-15--34,
                                         RetailNext B2B pivot, Handoffs
                                         1--4

  3.0       2026-03-07   Product Owner   Catalog coverage diagnosis,
                                         FR-C01--C07, NFR-11--14,
                                         Handoffs 5--6

  4.0       2026-03-07   Product Owner   AI Wardrobe tab: BR-21--28,
                                         FR-35--41, NFR-15--18, Handoff
                                         7 (8 tasks)

  **5.0**   2026-03-08   Product Owner   FR-42: GPT-4o + DALL-E 3
                                         Generative Try-On. BR-29,
                                         NFR-19, H7-09 added.
  --------- ------------ --------------- ------------------------------

**1. Feature Overview: AI Wardrobe Tab**

Version 4.0 introduced AI Wardrobe as a second primary destination
alongside AI Stylist. Version 5.0 enhances the Try It On section with a
GPT-4o + DALL-E 3 generative photo capability (FR-42).

AI Stylist = item-first. The user starts with a specific garment they
own or are considering. The AI finds what goes with it or similar items.
Each result has a Save to Wardrobe checkbox.

AI Wardrobe = occasion-first + creative. The user starts with an event
or mood in mind, discovers outfit pieces, builds a personal selection,
and sees how it looks on themselves --- including an AI-generated photo
via DALL-E 3.

**Navigation (Updated)**

Current: NEW ARRIVALS \| WOMEN \| MEN \| ACCESSORIES \| ✦ AI STYLIST \|
SALE

Updated: NEW ARRIVALS \| WOMEN \| MEN \| ACCESSORIES \| ✦ AI STYLIST \|
✦ AI WARDROBE (N) \| SALE

The (N) badge on AI WARDROBE is a live counter of items in the wardrobe
basket, updated in real-time whenever items are saved or removed from
either AI Stylist or AI Wardrobe Discover.

**2. Architecture Overview --- All Sections**

The wardrobe_basket in sessionStorage is the single source of truth
shared across AI Stylist and AI Wardrobe. Items saved in AI Stylist
appear in AI Wardrobe My Wardrobe, and vice versa.

  ----------------- ----------- ----------- -------------- -------------------
  **Destination**   **Section / **User      **Input        **Output**
                    Mode**      Intent**    Required**     

  ✦ AI STYLIST      Complete My Find what   Photo upload + 3--5 complementary
                    Outfit      goes with a optional       items with AI
                                specific    occasion text  rationale. Each
                                item                       card has a ☐ Save
                                                           to Wardrobe
                                                           checkbox.

  ✦ AI STYLIST      Find        Show more   Photo upload   6 visually similar
                    Similar     like this                  items ranked by
                    Items                                  score. Each card
                                                           has a ☐ Save to
                                                           Wardrobe checkbox.

  ✦ AI WARDROBE     ① Discover  Build an    Text           Curated item grid
                                outfit for  description of grouped by
                                an occasion occasion +     category. Each card
                                from        gender/style   has ☐ Save to
                                scratch     profile        Wardrobe. AI outfit
                                            (first-time    concept shown above
                                            modal)         grid.

  ✦ AI WARDROBE     ② My        View and    Items already  Editorial board
                    Wardrobe    manage all  in session     grouped by
                                saved items basket. No new category. Price
                                            input.         total. Shop All
                                                           CTA. Remove
                                                           individual items.

  ✦ AI WARDROBE     ③ Try It On See how     Gender (from   Phase 3: CSS
                                saved       profile).      composite overlay.
                                pieces look Choice: AI     Phase 3+: ✨
                                on me       model          Generate AI Photo
                                            illustration   button --- GPT-4o +
                                            OR user photo  DALL-E 3 generates
                                            upload.        a photorealistic
                                                           image of the user
                                                           wearing the saved
                                                           outfit.
  ----------------- ----------- ----------- -------------- -------------------

**3. Complete User Journey**

This table is the primary front-end reference for Handoff 7. Steps
1--10b are unchanged from v4.0. Step 11 is new in v5.0 (FR-42).

  -------- -------------- ------------------- --------------------------------------
  **\#**   **Location**   **User Action**     **System Response**

  1        Nav --- AI     User lands on AI    Unchanged from current UI. Two mode
           STYLIST        Stylist (current    cards: Complete My Outfit / Find
                          default page)       Similar Items.

  2        AI STYLIST --- User uploads a      Each result card now has a ☐ checkbox
           Result cards   shirt photo, clicks in the top-right corner. A counter
                          \'Find Matching     badge appears in the nav: \'AI
                          Pieces\', sees      WARDROBE ✦ (0)\'.
                          results             

  3        AI STYLIST --- User checks ☑ on 2  Badge updates live: \'AI WARDROBE ✦
           Checkboxes     items (e.g.         (2)\'. Items stored in
                          chinos + leather    sessionStorage(\'wardrobe_basket\').
                          belt)               

  4        Nav --- AI     User clicks \'✦ AI  AI Wardrobe page loads. If no
           WARDROBE       WARDROBE (2)\' in   gender/style profile exists → profile
                          the nav bar         modal shown first (one-time). After
                                              profile: user sees 3 sub-sections: ①
                                              Discover ② My Wardrobe (2) ③ Try It
                                              On.

  5        AI WARDROBE    User selects gender Profile saved to sessionStorage. Modal
           --- Profile    and style vibe      dismissed. Not shown again unless user
           Modal (first                       clicks \'Edit\'.
           time only)                         

  6        AI WARDROBE    User types:         System calls POST /wardrobe/discover.
           --- ① Discover \'Rooftop cocktail  Returns 20 items from full catalog
                          party, Barcelona,   grouped by category. AI outfit concept
                          late June.\'        shown above grid.

  7        AI WARDROBE    User checks ☑ on 3  My Wardrobe counter updates: \'My
           --- ① Discover more items from     Wardrobe (5)\'. Items added to shared
           checkboxes     discovery results   basket.

  8        AI WARDROBE    User clicks \'My    Full wardrobe board: all 5 saved items
           --- ② My       Wardrobe (5)\'      grouped by Topwear / Bottomwear /
           Wardrobe       sub-section         Footwear / Accessories. Price total
                                              shown. \'Shop All\' CTA. \'Try It On
                                              →\' button.

  9        AI WARDROBE    User clicks \'Try   Modal appears: \'How do you want to
           --- ③ Try It   It On →\'           try it on?\' Two option cards: (A) 👤
           On                                 Use AI Model \| (B) 📷 Upload Your
                                              Photo. Below option B: \'Your photo
                                              stays on your device --- never
                                              uploaded.\'

  10a      AI WARDROBE    User selects \'Use  Gender-appropriate model illustration
           --- ③ Try It   AI Model\'          displayed. Dominant garment from
           On (Model)                         wardrobe overlaid at torso via CSS.
                                              Label: \'✨ Generate AI Photo\' button
                                              available for AI-powered generation.

  10b      AI WARDROBE    User selects        Photo loaded client-side via
           --- ③ Try It   \'Upload Your       FileReader. CSS composite shown
           On (Own Photo) Photo\' and picks a immediately. \'✨ Generate AI Photo\'
                          JPEG                button appears below composite.
                                              Privacy notice visible.

  **11**   AI WARDROBE    User clicks \'✨    Spinner shown with 3-phase progress
           --- ③ Try It   Generate AI Photo\' messages: \'Analyzing your photo\... →
           On --- AI                          Building your outfit\... → Generating
           Generation                         your look\...\' (\~15--25s). DALL-E 3
                                              image displayed with label
                                              \'AI-generated preview --- Not a real
                                              photograph\'. \'Regenerate\' button
                                              available.
  -------- -------------- ------------------- --------------------------------------

**4. Business Requirements --- BR-21 to BR-29**

BR-29 is new in v5.0. All other BRs are unchanged from v4.0.

  -------- ------------------ ------------ ----------- ---------- ----------------- ------------------ --------
  **ID**   **Name**           **MoSCoW**   **Phase**   **Dep.**   **Description**   **Driver**         **FR**

  BR-21    Save-to-Wardrobe   Must         Phase 3     BR-23      Every result card Engagement,        FR-36a
           Checkboxes in AI                                       in AI Stylist     Session depth      
           Stylist                                                must have a ☐                        
                                                                  checkbox.                            
                                                                  Checking saves                       
                                                                  the item to a                        
                                                                  shared session                       
                                                                  wardrobe basket.                     
                                                                  A live counter                       
                                                                  badge on the AI                      
                                                                  WARDROBE nav item                    
                                                                  shows the current                    
                                                                  basket size.                         

  BR-22    AI Wardrobe Tab    Must         Phase 3     ---        A dedicated \'✦   UX clarity,        FR-41
           --- New                                                AI WARDROBE\'     Feature            
           Destination                                            link is added to  discoverability    
                                                                  the main                             
                                                                  navigation bar.                      
                                                                  It contains three                    
                                                                  sections: ①                          
                                                                  Discover, ② My                       
                                                                  Wardrobe, ③ Try                      
                                                                  It On.                               

  BR-23    Gender & Style     Must         Phase 3     BR-22      On first visit to Relevance,         FR-40
           Profile                                                AI Wardrobe, show Personalization    
           (first-time modal                                      a 2-step modal:                      
           in AI Wardrobe)                                        Step 1 --- gender                    
                                                                  identity. Step 2                     
                                                                  --- style vibe.                      
                                                                  Profile stored in                    
                                                                  sessionStorage.                      

  BR-24    AI Wardrobe --- ①  Must         Phase 3     BR-22      Inside AI         New-user           FR-35
           Discover: Occasion                                     Wardrobe, section conversion,        
           Text Input                                             ① Discover, users Inspiration        
                                                                  describe a social                    
                                                                  occasion in a                        
                                                                  free-text                            
                                                                  textarea. The                        
                                                                  system returns a                     
                                                                  curated grid of                      
                                                                  catalog items                        
                                                                  that together                        
                                                                  form a coherent                      
                                                                  outfit.                              

  BR-25    Save-to-Wardrobe   Must         Phase 3     BR-24      Every item card   Engagement,        FR-36b
           Checkboxes in                                          in the Discover   Cross-section      
           Discover                                               results grid has  journey            
                                                                  a ☐ checkbox that                    
                                                                  adds the item to                     
                                                                  the same shared                      
                                                                  wardrobe basket                      
                                                                  as AI Stylist                        
                                                                  checkboxes.                          

  BR-26    AI Wardrobe --- ②  Must         Phase 3     BR-22      Section ② My      AOV, Outfit        FR-37
           My Wardrobe:                                           Wardrobe shows    completion         
           Unified Board                                          all saved items                      
                                                                  from AI Stylist                      
                                                                  and Discover as                      
                                                                  an editorial                         
                                                                  board grouped by                     
                                                                  category. Footer:                    
                                                                  total price +                        
                                                                  Shop All CTA +                       
                                                                  Try It On button.                    

  BR-27    AI Wardrobe --- ③  Must         Phase 3     BR-22      Section ③ Try It  Emotional          FR-38
           Try It On: Model                                       On lets users     engagement, Trust  
           or Own Photo                                           visualise how                        
                                                                  their saved                          
                                                                  outfit looks on a                    
                                                                  human figure. Two                    
                                                                  options: (A) AI                      
                                                                  model                                
                                                                  illustration, (B)                    
                                                                  own photo upload.                    
                                                                  Phase 3: CSS                         
                                                                  composite                            
                                                                  overlay.                             

  BR-28    Try-On ---         Could        Phase 4     BR-27      Phase 4 upgrades  Differentiation,   FR-39
           Photorealistic AI                                      the composite     WOW factor         
           Upgrade                                                try-on to a                          
           (Replicate, Phase                                      photorealistic                       
           4)                                                     AI-generated                         
                                                                  image using a                        
                                                                  diffusion model                      
                                                                  (Replicate                           
                                                                  IDM-VTON or                          
                                                                  similar).                            

  BR-29    Try-On ---         Should       Phase 3     BR-27      When the user     Differentiation,   FR-42
           GPT-4o + DALL-E 3                                      uploads their     OpenAI demo        
           Generative Image                                       photo in Try It   coherence, WOW     
                                                                  On, a \'✨        factor             
                                                                  Generate AI                          
                                                                  Photo\' button                       
                                                                  triggers GPT-4o                      
                                                                  (vision) to                          
                                                                  analyze the user                     
                                                                  and build a                          
                                                                  styling prompt,                      
                                                                  then DALL-E 3                        
                                                                  generates a                          
                                                                  photorealistic                       
                                                                  image of the user                    
                                                                  wearing the saved                    
                                                                  outfit. Entirely                     
                                                                  within the OpenAI                    
                                                                  ecosystem. CSS                       
                                                                  composite (FR-38)                    
                                                                  remains as                           
                                                                  instant fallback.                    
  -------- ------------------ ------------ ----------- ---------- ----------------- ------------------ --------

**5. Functional Requirements --- FR-35 to FR-42**

**PREREQUISITE: FR-35 (POST /wardrobe/discover) and FR-42 (POST
/wardrobe/tryon-generative) both require the catalog to have ≥10K items
(Handoff 6 --- expand_catalog.py). Deploy Handoff 7 only after Handoff 6
is complete and embeddings have been regenerated.**

FR-42 is new in v5.0. All other FRs are unchanged from v4.0.

  -------- -------------------- -------------- ----------- -------- ---------------------------- --------------------- ---------
  **ID**   **Feature**          **Priority**   **Phase**   **BR**   **Description**              **Acceptance          **NFR**
                                                                                                 Criteria**            

  FR-35    POST                 Must           Phase 3     BR-24    New backend endpoint. Route: Returns ≥10 items     NFR-16
           /wardrobe/discover                                       POST /wardrobe/discover.     from ≥3 distinct      
           --- Occasion                                             Request: {occasion: str,     articleTypes for any  
           Discovery Endpoint                                       gender: str, style_vibe:     occasion input.       
                                                                    str, top_k: int = 20}.       outfit_concept is     
                                                                    Logic: (1) embed occasion    non-empty. Response   
                                                                    string via                   time \<8s. Requires   
                                                                    text-embedding-3-large; (2)  catalog ≥10K.         
                                                                    load full catalog embeddings                       
                                                                    from cache; (3) apply gender                       
                                                                    filter; (4) compute cosine                         
                                                                    similarity --- NO                                  
                                                                    articleType filter; (5)                            
                                                                    return top top_k items with                        
                                                                    score ≥ 0.25; (6) call                             
                                                                    GPT-4o-mini to generate                            
                                                                    outfit_concept (2--3                               
                                                                    sentences).                                        

  FR-36a   Save-to-Wardrobe     Must           Phase 3     BR-21    Add a ☐ checkbox to the      Checkbox visible on   ---
           Checkbox --- AI                                          top-right corner of every    all AI Stylist result 
           Stylist Result Cards                                     result card in AI Stylist.   cards. Basket updates 
                                                                    On check: push {id, name,    immediately on        
                                                                    articleType, image_url,      toggle. Nav badge     
                                                                    price, reason} to            reflects basket size. 
                                                                    sessionStorage               Warning toast at      
                                                                    wardrobe_basket. On uncheck: 20-item limit.        
                                                                    remove item by id. Update                          
                                                                    nav badge. Max 20 items.                           

  FR-36b   Save-to-Wardrobe     Must           Phase 3     BR-25    Identical checkbox behavior  Identical UX to       ---
           Checkbox --- AI                                          as FR-36a applied to every   FR-36a. Single basket 
           Wardrobe Discover                                        item card in the AI Wardrobe shared across both    
           Grid                                                     Discover results grid. Items sources. My Wardrobe  
                                                                    from both AI Stylist         counter updates live. 
                                                                    (FR-36a) and AI Wardrobe     Same 20-item limit    
                                                                    Discover (FR-36b) accumulate applies.              
                                                                    in the same sessionStorage                         
                                                                    wardrobe_basket array.                             

  FR-37    AI Wardrobe --- ② My Must           Phase 3     BR-26    Section ② My Wardrobe        Board renders all     FR-24
           Wardrobe Board                                           displays all items in the    basket items grouped  
                                                                    wardrobe basket. Layout:     by category. ✕        
                                                                    editorial board with         removes item and      
                                                                    category grouping (Topwear / updates counter.      
                                                                    Bottomwear / Footwear /      Price sum shown. Try  
                                                                    Accessories). Each item:     It On → navigates to  
                                                                    image thumbnail, product     section ③. Empty      
                                                                    name, articleType badge, ✕   state shown if basket 
                                                                    remove button. Footer: total is empty.             
                                                                    price sum + Shop All CTA +                         
                                                                    Try It On → button.                                

  FR-38    AI Wardrobe --- ③    Must           Phase 3     BR-27    Section ③ Try It On. Two     Two option cards      NFR-15,
           Try It On: CSS                                           option cards: (A) Use AI     shown. Correct gender NFR-18
           Composite (Phase 3)                                      Model --- display            model for option A.   
                                                                    model_male.png or            Photo loads           
                                                                    model_female.png based on    immediately on file   
                                                                    profile gender; (B) Upload   select (FileReader,   
                                                                    Your Photo --- file input,   \<200ms). Garment     
                                                                    photo loaded via FileReader  overlay renders       
                                                                    as base64, no fetch/XHR. In  within 500ms (CSS     
                                                                    both cases: determine        only, no API call).   
                                                                    dominant garment (priority:  Privacy notice        
                                                                    Dress \> Topwear \>          visible before file   
                                                                    Bottomwear \> Footwear).     selection.            
                                                                    Overlay dominant garment                           
                                                                    image via CSS                                      
                                                                    absolutely-positioned at                           
                                                                    torso zone. Secondary items                        
                                                                    shown as thumbnails below.                         
                                                                    This composite is the                              
                                                                    instant fallback for FR-42.                        

  FR-39    AI Wardrobe --- ③    Could          Phase 4     BR-28    Phase 4 upgrade to FR-38.    Generated image       NFR-15
           Try It On: AI                                            Backend: POST                displayed within 30s. 
           Generative                                               /wardrobe/tryon accepts      No visible artefacts  
           (Replicate, Phase 4)                                     {garment_image_base64,       on garment area.      
                                                                    person_image_base64,         person_image_base64   
                                                                    gender}. Calls Replicate     deleted server-side   
                                                                    fashn/tryon model. Returns   immediately after     
                                                                    {generated_image_base64}.    Replicate API         
                                                                    Graceful fallback to CSS     response --- never    
                                                                    composite on API timeout     stored. Fallback to   
                                                                    \>30s.                       composite shown on    
                                                                                                 API timeout.          

  FR-40    Gender & Style       Must           Phase 3     BR-23    Triggered on first           Modal shown only on   ---
           Profile Modal (first                                     navigation to AI Wardrobe if first visit. Both     
           visit to AI                                              sessionStorage               steps completable in  
           Wardrobe)                                                wardrobe_profile is absent.  \<20s. Profile        
                                                                    2-step modal: Step 1 --- 3   survives page refresh 
                                                                    large icon buttons: 👔 Men / within the same tab.  
                                                                    👗 Women / ✦ Non-binary.     \'Edit Profile\' link 
                                                                    Step 2 --- 5 style vibe      re-triggers modal.    
                                                                    tiles: Casual / Smart Casual Editing updates       
                                                                    / Formal / Sporty /          sessionStorage and    
                                                                    Streetwear. On confirm: save immediately affects   
                                                                    {gender, style_vibe} to      next Discover call.   
                                                                    sessionStorage                                     
                                                                    wardrobe_profile. Show Edit                        
                                                                    Profile link in AI Wardrobe                        
                                                                    page header.                                       

  FR-41    AI WARDROBE Nav      Must           Phase 3     BR-22    Add \'✦ AI WARDROBE\' as a   Nav link visible on   ---
           Link + Live Basket                                       nav bar link immediately     all pages. Badge      
           Counter Badge                                            after \'✦ AI STYLIST\'. The  count matches basket  
                                                                    link text includes a live    size at all times.    
                                                                    counter badge showing the    Clicking the link     
                                                                    current basket size: e.g.    navigates to the AI   
                                                                    \'✦ AI WARDROBE (3)\'. The   Wardrobe page. Badge  
                                                                    badge is updated reactively  updates without page  
                                                                    whenever sessionStorage      reload.               
                                                                    wardrobe_basket changes.                           

  FR-42    AI Wardrobe --- ③    Should         Phase 3     BR-29    Upgrade within FR-38 (same   AC-1: Generated image NFR-15,
           Try It On: GPT-4o +                                      Try It On section). When the matches person        NFR-19
           DALL-E 3 Generative                                      user has uploaded their      description (gender,  
           Photo                                                    photo AND clicks \'✨        skin tone visible,    
                                                                    Generate AI Photo\': (1)     body type approx).    
                                                                    Backend POST                 AC-2: At least 2      
                                                                    /wardrobe/tryon-generative   basket items          
                                                                    receives                     recognizable (correct 
                                                                    {person_image_base64,        color + garment       
                                                                    basket_items, gender,        type). AC-3: Total    
                                                                    style_vibe}. (2) Step 1:     time from click to    
                                                                    GPT-4o (vision) analyzes     image \<30s. AC-4:    
                                                                    user photo → outputs JSON    person_image_base64   
                                                                    {description: str} covering  not stored            
                                                                    body type, skin tone, hair,  server-side           
                                                                    age range --- no biometric   (verifiable in logs). 
                                                                    identifiers. (3) Step 2:     AC-5: Fallback to CSS 
                                                                    Build DALL-E 3 prompt from   composite activates   
                                                                    description + basket item    automatically on any  
                                                                    names + style_vibe:          API error. AC-6:      
                                                                    \"Fashion editorial          Disclaimer            
                                                                    photograph of                \"AI-generated · Not  
                                                                    \[description\] wearing      a real photograph\"   
                                                                    \[items\]. Full body shot,   always visible. AC-7: 
                                                                    natural lighting, white      Regenerate button     
                                                                    studio background, high      reuses cached         
                                                                    resolution, realistic fabric description without   
                                                                    texture.\" (4) Step 3: Call  re-uploading.         
                                                                    POST /v1/images/generations                        
                                                                    with model: \"dall-e-3\",                          
                                                                    size: \"1024x1792\",                               
                                                                    quality: \"standard\", n: 1.                       
                                                                    Cost: \~\$0.08/generation.                         
                                                                    (5) Return                                         
                                                                    {generated_image_url,                              
                                                                    prompt_used}. Frontend:                            
                                                                    spinner with 3-phase                               
                                                                    progress (\"Analyzing your                         
                                                                    photo\... Building your                            
                                                                    outfit\... Generating your                         
                                                                    look\...\"). Image displayed                       
                                                                    with label \"AI-generated                          
                                                                    preview --- Not a real                             
                                                                    photograph\". Regenerate                           
                                                                    button reuses cached GPT-4o                        
                                                                    description (sessionStorage,                       
                                                                    30min TTL) without                                 
                                                                    re-uploading photo.                                
                                                                    Fallback: if API fails or                          
                                                                    timeout \>30s, silently show                       
                                                                    CSS composite from FR-38                           
                                                                    with toast \"Generation                            
                                                                    failed --- showing preview                         
                                                                    instead\".                                         
                                                                    person_image_base64 never                          
                                                                    persisted server-side.                             
  -------- -------------------- -------------- ----------- -------- ---------------------------- --------------------- ---------

**6. Non-Functional Requirements --- NFR-15 to NFR-19**

NFR-19 is new in v5.0. All other NFRs are unchanged from v4.0.

  -------- -------------- -------------- ------------------------------- -----------
  **ID**   **Category**   **Priority**   **Requirement**                 **Phase**

  NFR-15   Try-On Privacy Must           Photos uploaded for the try-on  Phase 3/4
                                         are processed entirely          
                                         client-side (FileReader API,    
                                         base64 in memory). No photo     
                                         data is transmitted to any      
                                         server in Phase 3. In Phase 4   
                                         (Replicate API) and Phase 3+    
                                         (DALL-E 3 via FR-42), photos    
                                         sent to the API are deleted     
                                         server-side immediately after   
                                         the API response and never      
                                         persisted to disk or database.  
                                         A privacy notice must be shown  
                                         before the user selects a       
                                         photo.                          

  NFR-16   Wardrobe       Should         POST /wardrobe/discover must    Phase 3
           Discovery                     return items from ≥3 distinct   
           Relevance                     articleTypes in the top 10      
                                         results for any occasion input. 
                                         Measured against a test set of  
                                         10 diverse occasion             
                                         descriptions with catalog ≥10K. 
                                         This is why Handoff 6 (catalog  
                                         expansion) is a prerequisite.   

  NFR-17   Basket Session Must           wardrobe_basket and             Phase 3
           Persistence                   wardrobe_profile in             
                                         sessionStorage survive page     
                                         refresh within the same browser 
                                         tab. Both are cleared on tab    
                                         close (sessionStorage, not      
                                         localStorage --- no             
                                         cross-session persistence in    
                                         Phase 3). Basket state is never 
                                         stored server-side in Phase 3.  

  NFR-18   Try-On Render  Must           The composite try-on view (CSS  Phase 3
           Performance                   overlay, no API call) must      
                                         render the model + garment      
                                         overlay within 500ms of the     
                                         user selecting their option.    
                                         User photo must display within  
                                         200ms of file selection. No     
                                         spinner required for Phase 3    
                                         CSS composite rendering (it is  
                                         instant).                       

  NFR-19   AI Generation  Must           All images generated by DALL-E  Phase 3
           Transparency                  3 (FR-42) must show the label   
                                         \"AI-generated preview · Not a  
                                         real photograph\" permanently   
                                         and visibly --- before and      
                                         after generation. The DALL-E 3  
                                         prompt must never include real  
                                         biometric data --- only the     
                                         textual description produced by 
                                         GPT-4o vision. The system must  
                                         not present the generated image 
                                         as a real photograph of the     
                                         user in any UI element.         
  -------- -------------- -------------- ------------------------------- -----------

**7. Architectural Decision: FR-42 vs FR-39 (Replicate)**

FR-39 (planned Phase 4) uses Replicate IDM-VTON for pixel-accurate
inpainting. FR-42 (Phase 3, new) uses GPT-4o + DALL-E 3 entirely within
the OpenAI ecosystem. Both co-exist: FR-42 ships first as a Phase 3 demo
feature; FR-39 remains as the Phase 4 production upgrade path.

  ---------------- ------------------------ ------------------------
  **Dimension**    **FR-39 --- Replicate    **FR-42 --- GPT-4o +
                   IDM-VTON**               DALL-E 3 (v5.0)**

  Fidelity         High --- exact garment   Medium --- visual
                   pixel inpainting         interpretation of
                                            garment

  Stack            Replicate (external      100% OpenAI ecosystem
                   dependency)              

  Cost /           \~\$0.02--0.05           \~\$0.08 (DALL-E 3
  generation                                standard 1024×1792)

  Demo coherence   Requires justifying      Clean \"powered entirely
                   external vendor          by OpenAI\" narrative

  Latency          15--30s                  15--25s

  Natural fallback None                     Yes --- CSS composite
                                            from FR-38 always ready

  Phase            Phase 4                  Phase 3 (ships with
                                            Handoff 7)

  Recommendation   Future upgrade --- more  **✅ Ships now --- ideal
                   accurate but adds vendor for RetailNext demo.
                   dependency               Full OpenAI stack.**
  ---------------- ------------------------ ------------------------

**8. Handoff 7 --- Implementation Tasks for Claude Code**

9 ordered tasks (H7-01 to H7-09). Total estimated effort: \~16 hours (up
from \~13h in v4.0 --- H7-09 adds \~3h). Execute after Handoff 6
(catalog expansion to 10K items). Tasks are ordered by dependency.

MODEL ASSETS NOTE: H7-07 requires frontend/assets/models/model_male.png
and model_female.png. Generate as simple flat SVG silhouettes
(front-facing human figure, neutral clothing, light grey fill on white
background) exported as PNG 900×1400px. If complex, use a plain
light-grey rectangular silhouette as a CSS placeholder --- the overlay
logic works with any base image.

H7-09 NOTE: When the user selects \"Use AI Model\" (option A) rather
than uploading their own photo, the generative endpoint should be called
with a generic editorial prompt derived from gender + style_vibe (no
person_image_base64 required). This gives all users access to the DALL-E
3 feature, not just those who upload a photo.

  ---------- -------------------- -------------- ---------- -------- -----------------------------------------------------------
  **Task**   **Name**             **Priority**   **Est.**   **FR**   **Implementation Detail**

  H7-01      AI WARDROBE Nav      Must           0.5h       FR-41    In frontend/index.html add \'✦ AI WARDROBE\' to the nav bar
             Link + Badge                                            immediately after \'✦ AI STYLIST\'. Append a live counter
                                                                     badge in a \<span id=\'wardrobeCount\'\>. Create shared JS
                                                                     function updateWardrobeCount() that reads
                                                                     sessionStorage(\'wardrobe_basket\'), parses the JSON array,
                                                                     and updates the span text to \'(N)\'. Call
                                                                     updateWardrobeCount() on page load.

  H7-02      Checkboxes on AI     Must           2h         FR-36a   Add a checkbox input in the top-right corner of each result
             Stylist Result Cards                                    card. HTML: \<label class=\'save-checkbox\'\>\<input
                                                                     type=\'checkbox\'
                                                                     data-item-id=\'{id}\'/\>\<span\>Save\</span\>\</label\>. On
                                                                     change: if checked, push {id, name, articleType, image_url,
                                                                     price, reason} to sessionStorage(\'wardrobe_basket\'); if
                                                                     unchecked, remove by id. Call updateWardrobeCount() after
                                                                     each mutation. Show toast \'Saved to wardrobe\' / \'Removed
                                                                     from wardrobe\'. Enforce max 20 items.

  H7-03      AI Wardrobe Page     Must           2h         FR-40,   Create the AI Wardrobe page. Page structure: (1) Page
             Shell + Gender                                 FR-41    header: \'AI WARDROBE\' title + \'Edit Profile\' link. (2)
             Profile Modal                                           Three sub-section tabs: \[① Discover\] \[② My Wardrobe
                                                                     (N)\] \[③ Try It On\]. (3) Content area. On first load: if
                                                                     sessionStorage(\'wardrobe_profile\') is absent, show
                                                                     profile modal BEFORE rendering the page. Modal: Step 1 ---
                                                                     gender selector (👔 Men / 👗 Women / ✦ Non-binary). Step 2
                                                                     --- style vibe selector (5 tiles: Casual / Smart Casual /
                                                                     Formal / Sporty / Streetwear). Confirm saves to
                                                                     sessionStorage(\'wardrobe_profile\').

  H7-04      AI Wardrobe --- ①    Must           1.5h       FR-35,   Content of sub-section ① Discover. Show: (1) Profile
             Discover Section                               FR-36b   summary line: \'Discovering for: Women • Smart Casual
                                                                     \[Edit\]\'. (2) Large textarea with placeholder: \'Describe
                                                                     your occasion\... e.g. rooftop cocktail party in Barcelona,
                                                                     first date at a wine bar, job interview at a creative
                                                                     agency\'. (3) \'Find My Outfit\' button. On click: show
                                                                     spinner, POST to /wardrobe/discover with {occasion, gender,
                                                                     style_vibe, top_k: 20}. On response: show outfit_concept as
                                                                     italic styled quote above the grid; render item cards
                                                                     grouped by category with checkboxes (same basket as H7-02).

  H7-05      Backend: POST        Must           3h         FR-35    Create backend route POST /wardrobe/discover. Request body
             /wardrobe/discover                                      (Pydantic): {occasion: str, gender: str, style_vibe: str,
                                                                     top_k: int = 20}. Implementation: (1)
                                                                     get_embeddings(\[occasion\]); (2) load catalog DataFrame
                                                                     and embeddings pkl; (3) filter rows: keep gender-matching +
                                                                     Unisex --- NO articleType filter; (4) compute
                                                                     cosine_similarity_manual for all filtered rows; (5) sort
                                                                     descending, take top top_k with score \>= 0.25; (6) call
                                                                     GPT-4o-mini to generate outfit_concept 2--3 sentences; (7)
                                                                     return {outfit_concept: str, items: \[{id, name,
                                                                     articleType, baseColour, image_url, similarity_score,
                                                                     reason: \'\'}\]}.

  H7-06      AI Wardrobe --- ② My Must           2h         FR-37    Content of sub-section ② My Wardrobe. On load: read
             Wardrobe Section                                        sessionStorage(\'wardrobe_basket\'). If empty: show empty
                                                                     state. If not empty: render editorial board grouped by
                                                                     articleType. Category mapping: {Shirts, Tshirts, Tops,
                                                                     Blazers, Jackets, Kurtas, Sweaters → Topwear}, {Jeans,
                                                                     Trousers, Skirts, Shorts → Bottomwear}, {Casual Shoes,
                                                                     Formal Shoes, Heels, Flats, Sandals, Sports Shoes, Boots →
                                                                     Footwear}, {Watches, Handbags, Belts, Sunglasses, Caps,
                                                                     Scarves, Wallets, Jewellery → Accessories}. Each card:
                                                                     image, name, badge, ✕ remove button. Footer sticky bar:
                                                                     \'Total: £{sum}\' + \'Shop All\' button + \'Try It On →\'
                                                                     button (navigates to sub-tab ③).

  H7-07      AI Wardrobe --- ③    Must           2.5h       FR-38    Content of sub-section ③ Try It On. If basket has items:
             Try It On Section                                       show two option cards: (A) \'👤 Use AI Model\' --- render
             (CSS Composite)                                         model_male.png or model_female.png based on profile gender;
                                                                     (B) \'📷 Upload Your Photo\' --- file input, privacy
                                                                     notice: \'🔒 Your photo stays on your device. It is never
                                                                     uploaded to our servers.\' On file select: load via
                                                                     FileReader, display as base64 \<img\>. Try-On View:
                                                                     centered container, base image at fixed height (500px).
                                                                     Determine dominant garment (priority: Dress \> Topwear \>
                                                                     Shirt \> Blazer \> Bottomwear \> Footwear). Overlay
                                                                     dominant garment via CSS: position:absolute; top:15%;
                                                                     left:50%; transform:translateX(-50%); width:42%;
                                                                     opacity:0.92. Secondary items shown as thumbnails (60px)
                                                                     below. After both option A and option B: show \'✨ Generate
                                                                     AI Photo\' button (CTA primary style) below the composite.
                                                                     This button triggers H7-09.

  H7-08      Deep Link: Try It On Must           0.5h       FR-37,   The \'Try It On →\' button in sub-section ② My Wardrobe
             from My Wardrobe                               FR-38    must navigate to sub-section ③ Try It On. If sub-sections
                                                                     are tab-based (JS show/hide), switch the active tab. Ensure
                                                                     the basket state is not cleared during this navigation. The
                                                                     Try It On section must read the current basket immediately
                                                                     on activation without requiring a page reload.

  H7-09      Try It On ---        Should         3h         FR-42    Backend: Create POST /wardrobe/tryon-generative. Request
             GPT-4o + DALL-E 3                                       body (Pydantic): {person_image_base64: str, basket_items:
             Generative Photo                                        list\[{name, articleType, baseColour,
                                                                     productDisplayName}\], gender: str, style_vibe: str}.
                                                                     Implementation: (1) STEP 1 --- GPT-4o vision call:
                                                                     messages=\[{role:\'user\', content:\[{type:\'text\',
                                                                     text:\'You are a fashion photographer assistant. Analyze
                                                                     the person in this photo and describe them in 2-3 sentences
                                                                     covering: apparent body type, skin tone, hair color and
                                                                     length, approximate age range. Be factual and neutral.
                                                                     Output JSON only: {description: str}\'},
                                                                     {type:\'image_url\', image_url:{url:
                                                                     f\'data:image/jpeg;base64,{person_image_base64}\'}}\]}\].
                                                                     Parse {description}. (2) STEP 2 --- Build DALL-E 3 prompt:
                                                                     f\'Fashion editorial photograph of {description} wearing
                                                                     {item_list_str}. Full body shot, natural lighting, white
                                                                     studio background, high resolution, realistic fabric
                                                                     texture, {style_vibe} editorial style.\' item_list_str =
                                                                     \', \'.join(\[f\'{item.baseColour}
                                                                     {item.productDisplayName}\' for item in
                                                                     basket_items\[:5\]\]). (3) STEP 3 --- Call
                                                                     client.images.generate(model=\'dall-e-3\',
                                                                     prompt=dalle_prompt, size=\'1024x1792\',
                                                                     quality=\'standard\', n=1). Extract generated_image_url
                                                                     from response.data\[0\].url. (4) Return
                                                                     {generated_image_url: str, prompt_used: str}. Never persist
                                                                     person_image_base64 to disk or log. Frontend: \'✨ Generate
                                                                     AI Photo\' button visible below CSS composite (both for
                                                                     Model option and Own Photo option --- for Model option, no
                                                                     user photo is needed; use gender from profile to build a
                                                                     generic editorial prompt without person_image_base64). On
                                                                     click: show 3-phase spinner (\'Analyzing your photo\...\' →
                                                                     \'Building your outfit\...\' → \'Generating your
                                                                     look\...\'). On success: display generated image
                                                                     (max-width:400px) with permanent label \'AI-generated
                                                                     preview --- Not a real photograph\'. Show \'Regenerate\'
                                                                     button --- on click, call endpoint again (cache GPT-4o
                                                                     description in sessionStorage key \'tryon_description\'
                                                                     with 30min TTL to avoid re-analyzing the same photo). On
                                                                     error or timeout \>30s: show toast \'Generation failed ---
                                                                     showing preview instead\' and keep CSS composite visible.
  ---------- -------------------- -------------- ---------- -------- -----------------------------------------------------------

**9. Phase Delivery Plan --- Updated v5.0**

  ----------- --------------------- --------------- ---------------------
  **Phase**   **Sprint**            **Key FRs**     **Notes**

  Phase 3     Sprints 4--5 (Mar 22  FR-35,          Handoff 7 (H7-01 to
              -- Apr 4)             FR-36a/b,       H7-09). FR-42 / H7-09
                                    FR-37, FR-38,   adds \~3h to Sprint
                                    FR-40, FR-41,   4. Deploy after
                                    FR-42           Handoff 6 (10K
                                                    catalog).

  Phase 4     Sprint 7+ (TBD)       FR-39           Photorealistic try-on
                                                    via Replicate
                                                    IDM-VTON (Could
                                                    Have). Separate
                                                    budget approval
                                                    needed.
  ----------- --------------------- --------------- ---------------------

GPToutfit · Functional Requirements · v5.0 · Confidential
