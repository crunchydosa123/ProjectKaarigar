# GenAIExchange

# Some Points to be considered
Mock accounts :
username: surajchavan99886@gmail.com
pass:123456

Mock account2
username: ramu.deo@gmail.com
pass:123456


# Problem statement:

<img width="891" height="331" alt="image" src="https://github.com/user-attachments/assets/2aaf62c2-4b5e-45c0-ad25-638021b4d0bf" />

## Our Team:

<img width="1053" height="585" alt="image" src="https://github.com/user-attachments/assets/826062ac-98d7-4efa-9244-a3a16770124e" />

# Introduction:

Local artisans possess incredible skill and create unique products, but often face significant hurdles in navigating the complex digital world.  
From building an online brand and creating engaging social media content to optimizing product listings and analyzing sales, the **technical barriers can be overwhelming**.

**Project Karigar** is an **end-to-end solution** that acts as a digital companion for these artisans.  
We replace complex forms and software with an **intuitive, conversational AI** that understands their language and needs.  

Our platform automates:
- Content creation  
- Marketing  
- Marketplace listings  
- Intelligent insights  

…allowing artisans to focus on what they do best: **creating**.

---

# Product Summary

<img width="1196" height="674" alt="image" src="https://github.com/user-attachments/assets/1c6153b0-6032-482d-a249-2be4a6cb88ba" />


## Who is it for?

**Project Kaarigar** is built for:

- **Artisans** (handcrafted makers, solo creators)  
- **Small businesses** (micro-brands wanting to go online)  
- **Homemakers / Hobbyists** who want to sell their creations  

Mobile-first, multilingual, and designed for users with minimal technical experience.

---

## Areas of User Impact

- **Original, consistent brand identity** — conversational onboarding builds a polished brand persona without forms.  
- **Optimized marketplace listings** — SEO-ready titles & descriptions tailored to each platform.  
- **Improved digital content quality** — AI-generated product photos, backdrops and marketing videos.  
- **Data simplified into actionable insights** — sales & trend analytics converted into pricing, content and growth recommendations.

---

# What does Project Kaarigar do today?

### Conversational Brand Onboarding
Streamlines artisan onboarding via a conversational interview that generates a **personalized brand document and profile**, ensuring consistent branding across the app and listings.

### AI Content Generation & Natural Language Editing Support
Generates **platform-specific AI photos and videos** for product shoots and marketing.  
Supports natural-language editing commands (e.g. “shorten this video and add retro music”) executed via our **FFmpeg + Gemini modules** to produce ready-to-post media.

### AI-based SEO-optimized Listing with Marketplace Integrations
Transforms product images and descriptions into **high-ranking, SEO-optimized listings**, then automatically posts them to multiple marketplaces and channels (WhatsApp, Amazon, Flipkart, Instagram, etc.).

### Multi-channel Commerce & Social Media Engine
Analyzes social and marketplace trends to suggest content, automates posting and ad campaigns, and manages **direct sales & payments** using an integrated WhatsApp bot and other commerce connectors.

### Direct Social Media Sales & Order Management with Agentic Insights
Converts sales and engagement data into **smart pricing advice** and **data-driven content suggestions** to increase conversions and revenue.  
Provides end-to-end support from **discovery → listing → sale → fulfillment**.

---

## 🎥 Video Demo
[Watch the demo](https://www.youtube.com/watch?v=eVoegX7q474)

---

# How we differ from existing solutions:

<img width="1193" height="671" alt="image" src="https://github.com/user-attachments/assets/12741623-81a7-4273-aa0b-26c2956be643" />

---

As the comparison shows, the ecosystem today is **fragmented** — marketplaces, social platforms, and editing tools each provide pieces of the value chain.  


**Project Kaarigar** combines the missing pieces into a single productised flow, adding **conversational onboarding**, **end-to-end marketplace listing + outreach**, **agentic insights**, and **natural-language media generation**.

---

### **Unique End-to-End Onboarding**
**Project Kaarigar** is the only solution in this comparison that provides **conversational onboarding** that outputs a consistent **brand document and profile**.

### **Unified Media Workflow**
We combine **AI Camera Assist**, **Veo/FFmpeg natural-language editing**, and **Gemini-driven content ideation** so artisans can **capture, generate, and edit platform-ready media** without switching apps.

### **Marketplace-First Distribution**
While some platforms may offer bits of media tooling or analytics, **Project Kaarigar** is the only product that automates **SEO-ready listing generation**, **posting**, and **outreach**, closing the loop from **creation → listing → sale**.

### **Agentic Insights**
We turn **sales and trend signals** into actionable, **artisan-specific recommendations** (pricing, content, promotions) powered by **Gemini**.

---

**Project Kaarigar** provides support to artisans **across marketplaces, social channels, and editing workflows**, enabling even the smallest businesses to reach customers with **professional media**, **optimized listings**, and **data-driven growth**.


**In short:** We replace **complexity** with a **single, intelligent assistant** , designed exclusively for the artisan.

---
# List Of Features:
<img width="1090" height="617" alt="image" src="https://github.com/user-attachments/assets/4464f28c-ebcc-41ef-9790-e1d32c206bb6" />


# Architecture
![GenAI Exchange-Page-9](https://github.com/user-attachments/assets/6f82dd99-0f92-4b51-bc04-3383dd0dc150)

# Use Case Diagram:
<img width="1243" height="752" alt="image" src="https://github.com/user-attachments/assets/c03c45f1-0b45-4679-86c7-94e0bc7f775c" />

---

# Google Cloud & AI Tools Usage

<img width="1190" height="672" alt="image" src="https://github.com/user-attachments/assets/e7bd7ec5-f705-4092-a090-375bf685b188" />


---

**Project Kaarigar** leverages a suite of **Google Cloud services** and **generative AI models** to power an end-to-end pipeline for onboarding, media generation, listing creation, analytics, and distribution.

---

### **Core Platform Services**

- **Cloud Functions** — Event-driven glue that automates preprocessing, content generation, and posting via **serverless, asynchronous workflows**.  
- **Cloud Run** — Runs **decoupled microservices** for AI inference, video generation, and trend analysis with **scalable reliability**.  
- **Firestore** — Stores **artisan, product, and brand data** with integrity and enables **semantic search** using **Vertex AI embeddings**.  
- **Cloud Storage** — Hosts all media assets (**images, videos, creatives**) for **scalable access, analytics, and real-time content delivery**.

---

### **Generative AI Models & Media Tooling**

- **Gemini 2.5 Flash-Lite** — Conversationally generates **brand documents**, **product descriptions**, **captions**, and **short marketing content** from artisan inputs.  
- **Gemini 2.5 Pro** — Produces **long-form creative** and **video-ready scripts** from brand documents and campaign ideas.  
- **Gemini Audio Native Dialog** — Powers **voice-based onboarding** and **natural spoken interactions** for **multilingual artisan experiences**.  
- **Google Veo 3** — Creates and enhances **AI-driven videos** of artisan products and marketing shoots.  
- **Imagen 4** — Generates and edits **high-quality product photos** for **consistent visual branding** and **marketplace listings**.  
- **Google Cloud Text-to-Speech** — Converts generated or conversational text into **natural voice** for audio content and hands-free interaction.

---

### **Intelligence & Personalization**

- **Vertex AI (Embeddings + AI Services)** — Provides **semantic understanding**, **recommendations**, and **personalization** through embeddings and model APIs that enable **RAG**, **similarity search**, and **tailored suggestions**.

---

## Tech Stack Deep Dive:
<img width="1195" height="670" alt="image" src="https://github.com/user-attachments/assets/903b9aa1-b7f9-4a0d-a30d-97da825710ec" />

---

Our stack is now fully **serverless + container-first** on **Cloud Run**, with **Firestore + Cloud Storage** as the primary data layer and a set of **Cloud Run microservices** for each AI capability.

---

### 🖥️ Frontend
- **React** — Mobile-first, component-driven UI.  
- **Tailwind CSS** — Fast, consistent styling.  
- **Hosting:** Frontend runs as a container on **Cloud Run**.

---

### ⚙️ Backend & Media
- **Python (+ Flask / microservices)** — Lightweight APIs and orchestration.  
- **FFmpeg** — Media encoding, trimming, and edits driven by natural language commands (deployed inside the video/image editing Cloud Run service).  
- **Container Image Registry:** **Artifact Registry** for storing Docker images.

---

### 🗂️ Database & Storage
- **Google Firestore** — Stores artisan, product, and brand metadata; used for fast lookups and user/profile data.  
- **Google Cloud Storage** — Hosts all media assets (images, videos, creatives) for scalable delivery and processing.

---

### ☁️ Deployment & Hosting
- **Cloud Run** — Primary runtime for decoupled microservices:
  - Conversational Agent  
  - Camera Agent  
  - Video/Image Editing  
  - Listings Generator  
  - AI Analytics  
  - WhatsApp Campaign  
  - Frontend  
  Each service runs as a container for **easy CI/CD** and **independent scaling**.  
- **CI/CD** — GitHub (or equivalent) → **Artifact Registry** → **Cloud Run** for rolling updates and automated deployments.

---

### 🤖 Google AI Tools (Vertex AI + Models)
- **Gemini 2.5 Flash-Lite** — Conversational generation: brand docs, short captions, product descriptions, and on-the-fly content edits.  
- **Gemini 2.5 Pro** — Long-form creative, campaign ideas, and video-ready scripts.  
- **Gemini Audio / Native Dialog** — Voice-based onboarding and multilingual spoken interactions.  
- **Google Veo 3** — AI video generation & enhancement for product shoots and promos.  
- **Imagen 4** — High-quality product photo generation and editing for consistent marketplace visuals.  
- **Google Cloud Text-to-Speech** — Converts generated text into natural voice for camera assist and hands-free UX.  
- **Vertex AI (Embeddings + Services)** — Semantic understanding, RAG workflows, personalization, and recommendation pipelines.

---

## 🔄 Hosting & Rolling Out Updates (How Services Map)
Multiple **Cloud Run** services each handle a focused responsibility:
- **Conversational Agent** — Gemini-powered onboarding.  
- **Camera Agent** — Voice + camera instructions / capture assist.  
- **Video & Image Editing** — FFmpeg + Veo + Imagen workflows.  
- **AI Analytics** — Trend analysis and pricing signal generation.  
- **Listings Generation** — SEO titles, descriptions, and marketplace integrations.  
- **WhatsApp Campaign** — Automated outreach and direct-sales flow.  

The **Frontend** is deployed as a Cloud Run container that communicates with backend microservices.  
**CI/CD** pipelines push container images to **Artifact Registry** and perform **rolling updates** to Cloud Run services.

---

# User Experience

<img width="1191" height="671" alt="image" src="https://github.com/user-attachments/assets/0563d8eb-b13a-4d8a-af5b-eda2dd13b4f3" />
---

**Project Kaarigar** is designed to make digital commerce effortless for artisans by combining conversational AI, multimodal media tools, and marketplace automation into a simple, mobile-first experience.

---

### AI-Assisted Seamless Journey
Delivers a consistent, guided workflow from **conversational onboarding** through **listing management and marketing**, minimizing cognitive load and manual steps for the artisan.


### Conversational Platform
Offers an interactive, **natural-language platform** that uses **voice-based dialogs (Gemini Audio / Native Dialog)** to simplify complex tasks like **branding** and **sales management**.


### Multilingual & Responsive Design
Ensures an intuitive, adaptable interface using **React** and **Tailwind CSS** that works flawlessly across all devices (**mobile-first**) and supports **multiple regional languages**.


### Effortless Content Creation
Artisans can generate professional, platform-specific **product photos (Imagen 4)** and **marketing videos (Veo 3)** using **simple natural-language commands** — reducing time and producing consistent creative assets.


### Guided Workflow & Market Integration
Provides a structured, **step-by-step journey** that guides artisans from raw craft to **automatically posted, SEO-optimized listings** across multiple marketplaces.


### Agentic Hands-Free Interaction
Leverages **voice-based Camera Assist** for **natural spoken interactions** and **in-context content editing**, making the digital process accessible even while the artisan is actively working.

---

# Market & Adoption

<img width="1195" height="671" alt="image" src="https://github.com/user-attachments/assets/2f7233c0-12c2-4388-a040-31d022274af7" />


### 30–90 Day Playbook (Try / Launch / Measure)

---

#### **Day 0–30 — Test & measure with select users**
- Release the current version of **Project Kaarigar** to selected audiences for **usability testing** and **feature validation**.  
- Run focused **usability sessions** and **in-person workshops** to test content creation flows, onboarding, and listing posting.  
- Collect feedback on **pain points**, **UX friction**, and **most-valued features**.


#### **Day 31–60 — Iterate features & scale cloud deployment**
- Prioritize and double down on features users love; remove or rework parts that don’t serve the core value.  
- Harden **cloud deployment** for scale and cost efficiency (**Cloud Run autoscaling**, **CI/CD**, **Artifact Registry**).  
- Optimize **media generation pipelines** and monitor **AI usage patterns** to control costs.


#### **Day 61–90 — Launch app on Play Store**
- Publish the **mobile app** to **Play Store** (and **App Store** if planned).  
- Open broader beta, enable onboarding campaigns, and measure **activation → listing → sale** funnel metrics.  
- Ramp up **partner outreach** and **community acquisition programs**.

---

### First Users — Who & How We’ll Approach Them


#### **Artisans Registered with NGOs**
- Partner with **2–3 key NGOs** for direct access and trust.  
- Run **in-person workshops** to onboard the first **~100 users**, gather qualitative feedback, and build advocacy.


#### **Hobbyists / Homemakers Struggling to Sell**
- Target online communities (**Facebook**, **Instagram groups**, **Reddit**) with an **exclusive beta offer**.  
- Provide a free **“Launch Your Shop” guide** and lightweight onboarding to drive **low-cost digital acquisition**.


#### **Women’s Savings & Local Community Groups**
- Work with **local community leaders** in a **target geographic cluster**.  
- Run **small, trusted group meetings** to demonstrate **financial benefits** and drive **local adoption**.

---

# Camera Agent Walkthrough

Please take a look at this video to get a detailed overview of how our specialized camera agent helps artisans navigate complex photo and video shoots with ease and get the best possible results.

Video Link - [Watch the demo](https://youtu.be/vf5IxlNhGro)

---

# Implementation and WireFrames

<img width="1088" height="607" alt="image" src="https://github.com/user-attachments/assets/018cb8e7-22c0-4b5f-b6e3-de6d321c446c" />

---


# ✅ Conclusion
**Project Karigar** is not just a tool it’s an **ecosystem**.  
We empower artisans by:  
- Preserving **authenticity**  
- Providing **AI-driven content & insights**  
- Ensuring **scalability** and **ease of adoption**  

> Crafted in India, scaled for the world 🌍

