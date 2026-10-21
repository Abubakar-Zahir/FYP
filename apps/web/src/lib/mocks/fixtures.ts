import type {
  AnalyticsOverview,
  CommentSummary,
  CommentTheme,
  DnaRecord,
  Experiment,
  Me,
  Reel,
  Script,
  WeeklyReport,
} from "@/lib/api/types";

export const meFixture: Me = {
  id: "usr_01",
  name: "Ayesha Khan",
  email: "ayesha@example.com",
  profile: null,
  instagram: null,
};

export const connectedInstagram: NonNullable<Me["instagram"]> = {
  username: "ayesha.eats.lahore",
  account_type: "CREATOR",
  trial_reels_eligible: true,
};

export const reelsFixture: Reel[] = [
  {
    id: "reel_01",
    caption: "Anarkali ki sab se crispy samosa chaat? 🥟 Rs 150 mein full value",
    posted_at: "2026-10-18T14:00:00Z",
    hook_type: "question",
    views: 184200,
    saves: 9120,
    shares: 4310,
    avg_watch_time_s: 11.4,
    outlier_score: 3.4,
  },
  {
    id: "reel_02",
    caption: "3 nihari spots in Lahore ranked — #1 will surprise you",
    posted_at: "2026-10-15T13:30:00Z",
    hook_type: "list",
    views: 96500,
    saves: 7800,
    shares: 2105,
    avg_watch_time_s: 13.2,
    outlier_score: 1.8,
  },
  {
    id: "reel_03",
    caption: "Maine 1 din sirf Rs 500 mein khana khaya. Possible hai?",
    posted_at: "2026-10-12T15:10:00Z",
    hook_type: "story",
    views: 61300,
    saves: 2210,
    shares: 980,
    avg_watch_time_s: 16.8,
    outlier_score: 1.1,
  },
  {
    id: "reel_04",
    caption: "Stop ordering biryani from apps. Do this instead 👇",
    posted_at: "2026-10-09T12:45:00Z",
    hook_type: "bold_claim",
    views: 42100,
    saves: 1830,
    shares: 640,
    avg_watch_time_s: 8.9,
    outlier_score: 0.8,
  },
  {
    id: "reel_05",
    caption: "Gawalmandi food street at 2am 🌙",
    posted_at: "2026-10-06T21:00:00Z",
    hook_type: "pattern_interrupt",
    views: 38800,
    saves: 1140,
    shares: 410,
    avg_watch_time_s: 7.2,
    outlier_score: 0.7,
  },
];

function buildTrend(days: number): AnalyticsOverview["trend"] {
  const start = new Date("2026-09-22T00:00:00Z").getTime();
  const dayMs = 86_400_000;
  return Array.from({ length: days }, (_, index) => {
    const wave = Math.sin(index / 3) * 9000 + Math.cos(index / 7) * 5000;
    const growth = index * 750;
    const spike = index === 26 ? 60000 : index === 23 ? 28000 : 0;
    return {
      date: new Date(start + index * dayMs).toISOString(),
      views: Math.round(24000 + wave + growth + spike),
    };
  });
}

export const overviewFixture: AnalyticsOverview = {
  period_days: 30,
  totals: { views: 1_284_600, reach: 742_300, saves: 38_420, shares: 15_870, avg_watch_time_s: 11.6 },
  change: { views: 0.32, reach: 0.21, saves: 0.47, shares: 0.18, avg_watch_time_s: -0.06 },
  trend: buildTrend(30),
  best_formats: [
    { hook_type: "question", reels: 6, median_outlier: 2.4 },
    { hook_type: "list", reels: 5, median_outlier: 1.7 },
    { hook_type: "story", reels: 4, median_outlier: 1.1 },
    { hook_type: "bold_claim", reels: 7, median_outlier: 0.9 },
    { hook_type: "pattern_interrupt", reels: 3, median_outlier: 0.7 },
  ],
};

export const dnaFixture: DnaRecord[] = [
  {
    id: "dna_01",
    schema_version: "1.0",
    title: "Samosa chaat price reveal",
    source: "own",
    hook_type: "question",
    hook_text: "Anarkali ki sab se crispy samosa chaat?",
    pacing_cuts_per_10s: 4.2,
    length_s: 28,
    beats: [
      { label: "Hook", start_s: 0, end_s: 3, description: "Close-up crunch with question on screen" },
      { label: "Context", start_s: 3, end_s: 8, description: "Walk-in shot, stall name and location" },
      { label: "Proof", start_s: 8, end_s: 20, description: "Three quick bites, reaction, texture shots" },
      { label: "Payoff", start_s: 20, end_s: 25, description: "Price reveal: Rs 150" },
      { label: "CTA", start_s: 25, end_s: 28, description: "Save for your next Anarkali trip" },
    ],
    overlays: [
      { at_s: 0, text: "Sab se crispy?" },
      { at_s: 4, text: "📍 Anarkali Bazaar" },
      { at_s: 21, text: "Sirf Rs 150" },
    ],
    cta: "Save this for your next Anarkali trip",
    outlier_score: 3.4,
    transcript:
      "Anarkali ki sab se crispy samosa chaat? Chalo dekhte hain. Ye stall 30 saal purana hai... crunch suno! Chutney perfect balance hai, na zyada meethi na teekhi. Aur price? Sirf 150 rupay. Save kar lo next trip ke liye.",
    is_template: true,
  },
  {
    id: "dna_02",
    schema_version: "1.0",
    title: "Nihari ranking",
    source: "own",
    hook_type: "list",
    hook_text: "3 nihari spots in Lahore ranked",
    pacing_cuts_per_10s: 3.1,
    length_s: 41,
    beats: [
      { label: "Hook", start_s: 0, end_s: 3, description: "Three bowls side by side, numbers on screen" },
      { label: "#3", start_s: 3, end_s: 14, description: "Spot three with one-line verdict" },
      { label: "#2", start_s: 14, end_s: 26, description: "Spot two with price and wait time" },
      { label: "#1", start_s: 26, end_s: 37, description: "Winner reveal with slow-motion pour" },
      { label: "CTA", start_s: 37, end_s: 41, description: "Comment your favourite" },
    ],
    overlays: [
      { at_s: 0, text: "Ranked 🔥" },
      { at_s: 26, text: "#1 😮" },
    ],
    cta: "Comment your favourite nihari spot",
    outlier_score: 1.8,
    transcript:
      "3 nihari spots in Lahore ranked. Number 3... solid, but the gravy is too oily. Number 2, Rs 450, 20 minute wait, worth it. Number 1 — ye wali nalli dekho. Comment karo apni favourite.",
    is_template: false,
  },
  {
    id: "dna_03",
    schema_version: "1.0",
    title: "Reference: 24h budget challenge",
    source: "reference",
    hook_type: "story",
    hook_text: "I lived on Rs 500 for a whole day",
    pacing_cuts_per_10s: 5.6,
    length_s: 52,
    beats: [
      { label: "Hook", start_s: 0, end_s: 4, description: "Cash in hand, stakes stated" },
      { label: "Setup", start_s: 4, end_s: 12, description: "Rules of the challenge" },
      { label: "Journey", start_s: 12, end_s: 42, description: "Breakfast, lunch, dinner with running total" },
      { label: "Twist", start_s: 42, end_s: 48, description: "Money left over, surprise purchase" },
      { label: "CTA", start_s: 48, end_s: 52, description: "Follow for part 2" },
    ],
    overlays: [
      { at_s: 0, text: "Rs 500 / 24h" },
      { at_s: 12, text: "Spent: Rs 120" },
      { at_s: 30, text: "Spent: Rs 340" },
    ],
    cta: "Follow for part 2",
    outlier_score: 2.9,
    transcript:
      "I lived on Rs 500 for a whole day. Rules: no home food, no friends paying. Breakfast halwa puri, Rs 120... lunch daal chawal... and I still had money left.",
    is_template: false,
  },
  {
    id: "dna_04",
    schema_version: "1.0",
    title: "Reference: Don't order this",
    source: "reference",
    hook_type: "bold_claim",
    hook_text: "Stop ordering biryani from apps",
    pacing_cuts_per_10s: 6.3,
    length_s: 24,
    beats: [
      { label: "Hook", start_s: 0, end_s: 2, description: "Hand pushes phone away" },
      { label: "Problem", start_s: 2, end_s: 9, description: "Soggy delivery biryani comparison" },
      { label: "Fix", start_s: 9, end_s: 21, description: "Three local places that pack well" },
      { label: "CTA", start_s: 21, end_s: 24, description: "Share with your biryani friend" },
    ],
    overlays: [{ at_s: 0, text: "❌ Stop" }],
    cta: "Share with your biryani friend",
    outlier_score: 0.8,
    transcript: "Stop ordering biryani from apps. Ye dekho delivery wali biryani... soggy. Instead, ye teen jagah try karo.",
    is_template: false,
  },
  {
    id: "dna_05",
    schema_version: "1.0",
    title: "Food street night walk",
    source: "own",
    hook_type: "pattern_interrupt",
    hook_text: "Gawalmandi at 2am",
    pacing_cuts_per_10s: 7.1,
    length_s: 33,
    beats: [
      { label: "Hook", start_s: 0, end_s: 2, description: "Sudden cut from dark street to sizzling tawa" },
      { label: "Tour", start_s: 2, end_s: 28, description: "Fast montage of five stalls" },
      { label: "CTA", start_s: 28, end_s: 33, description: "Tag your night-owl friend" },
    ],
    overlays: [{ at_s: 0, text: "2:00 AM 🌙" }],
    cta: "Tag your night-owl friend",
    outlier_score: 0.7,
    transcript: "Gawalmandi, raat ke do baje. Tawa chicken, kulfi, paye... Lahore kabhi nahi sota.",
    is_template: false,
  },
];

export function buildScript(id: string, templateId: string, topic: string, language: Script["language"]): Script {
  const roman = language !== "english";
  return {
    id,
    template_id: templateId,
    topic,
    language,
    model_version: "script-gen-0.1+llm-mock",
    hooks: [
      {
        text: roman ? `${topic} — kya ye hype ke qabil hai?` : `Is ${topic} actually worth the hype?`,
        score: 84,
        top_factors: [
          { label: "Question hook (your best format)", impact: 0.31 },
          { label: "Price or value cue", impact: 0.18 },
          { label: "Under 8 words", impact: 0.09 },
        ],
      },
      {
        text: roman ? `Maine ${topic} 3 jagah try kiya. Result shocking tha` : `I tried ${topic} at 3 places. The result shocked me`,
        score: 77,
        top_factors: [
          { label: "Story setup with stakes", impact: 0.24 },
          { label: "Number in the hook", impact: 0.15 },
          { label: "Longer than 10 words", impact: -0.06 },
        ],
      },
      {
        text: roman ? `Lahore ka sab se underrated ${topic}` : `Lahore's most underrated ${topic}`,
        score: 71,
        top_factors: [
          { label: "Local place name", impact: 0.2 },
          { label: "Superlative claim", impact: 0.12 },
          { label: "No question or number", impact: -0.08 },
        ],
      },
      {
        text: roman ? `${topic} sirf Rs 200 mein? 🤯` : `${topic} for just Rs 200? 🤯`,
        score: 66,
        top_factors: [
          { label: "Price or value cue", impact: 0.22 },
          { label: "Emoji in hook text", impact: 0.04 },
          { label: "Similar to last 3 posts", impact: -0.11 },
        ],
      },
      {
        text: roman ? `Ye ${topic} mistake sab karte hain` : `Everyone makes this ${topic} mistake`,
        score: 52,
        top_factors: [
          { label: "Bold claim (weaker format for you)", impact: -0.14 },
          { label: "Curiosity gap", impact: 0.12 },
          { label: "Generic wording", impact: -0.07 },
        ],
      },
    ],
    angles: [
      { title: "Price reveal", summary: "Build up quality first, reveal the low price as the payoff." },
      { title: "Head-to-head", summary: "Compare two famous spots, let viewers vote in comments." },
      { title: "Hidden gem", summary: "Take viewers somewhere they have never heard of, end on location." },
    ],
    body: [
      {
        beat: "Hook",
        line: roman ? `${topic} — kya ye hype ke qabil hai?` : `Is ${topic} actually worth the hype?`,
        shot: "Extreme close-up, first bite, question on screen",
      },
      {
        beat: "Context",
        line: roman ? "Ye jagah 25 saal se yahin hai, aur line dekho." : "This place has been here 25 years. Look at that line.",
        shot: "Walk-in, signboard, queue",
      },
      {
        beat: "Proof",
        line: roman ? "Texture suno... aur masala bilkul balanced." : "Listen to that crunch... and the spice is perfectly balanced.",
        shot: "Three fast cuts: bite, texture, reaction",
      },
      {
        beat: "Payoff",
        line: roman ? "Aur price? Sirf 200 rupay." : "And the price? Just Rs 200.",
        shot: "Receipt or price board, text overlay",
      },
      {
        beat: "CTA",
        line: roman ? "Save karo aur us dost ko bhejo jo hamesha bhooka hota hai." : "Save this and send it to your always-hungry friend.",
        shot: "Talking head, point at screen",
      },
    ],
  };
}

export const experimentFixture: Experiment = {
  id: "exp_01",
  video_title: "Samosa chaat price reveal — v2",
  strategy: "thompson_sampling",
  winner_variant_id: null,
  variants: [
    {
      id: "var_a",
      label: "A",
      hook_line: "Anarkali ki sab se crispy samosa chaat?",
      opener: "Crunch close-up",
      caption: "Rs 150 mein itna crunch? 🥟 Save for your next Anarkali trip #lahorefood",
      is_trial: true,
      status: "draft",
      insights: [],
    },
    {
      id: "var_b",
      label: "B",
      hook_line: "Is this Lahore's best Rs 150 snack?",
      opener: "Price board first",
      caption: "Best Rs 150 you'll spend in Lahore? 👀 #streetfood #lahore",
      is_trial: true,
      status: "draft",
      insights: [],
    },
    {
      id: "var_c",
      label: "C",
      hook_line: "30 saal purana stall, aur abhi bhi #1",
      opener: "Stall owner smiling",
      caption: "30 saal se same taste ❤️ Anarkali legends #foodpk",
      is_trial: true,
      status: "draft",
      insights: [],
    },
  ],
};

export const experimentInsights: Record<string, Experiment["variants"][number]["insights"]> = {
  var_a: [
    { window: "24h", views: 4200, reach: 3900, saves: 210, shares: 96 },
    { window: "72h", views: 11800, reach: 10400, saves: 640, shares: 290 },
  ],
  var_b: [
    { window: "24h", views: 3100, reach: 2950, saves: 120, shares: 54 },
    { window: "72h", views: 7300, reach: 6800, saves: 290, shares: 130 },
  ],
  var_c: [
    { window: "24h", views: 5600, reach: 5100, saves: 330, shares: 150 },
    { window: "72h", views: 15900, reach: 14200, saves: 910, shares: 420 },
  ],
};

export const commentThemesFixture: CommentTheme[] = [
  {
    id: "th_01",
    theme: "Where is this place?",
    size: 412,
    dominant_label: "question",
    examples: ["Ye kahan hai exact location?", "Address plz 🙏", "Is this near Mall Road?"],
    idea: "Pin a map card at the end of every food reel and do a 'locations recap' reel.",
  },
  {
    id: "th_02",
    theme: "Try spots in other cities",
    size: 268,
    dominant_label: "request",
    examples: ["Karachi ka bhi review karo", "Islamabad aao kabhi!", "Pindi mein bhi aisi chaat hai"],
    idea: "Karachi vs Lahore samosa chaat face-off, collab with a Karachi creator.",
  },
  {
    id: "th_03",
    theme: "Love the honest reviews",
    size: 231,
    dominant_label: "praise",
    examples: ["Finally koi honest review deta hai", "Your reactions are the best 😂", "Bohat acha content"],
    idea: "Make 'honest rating' a recurring segment with a fixed score card.",
  },
  {
    id: "th_04",
    theme: "Prices seem wrong",
    size: 97,
    dominant_label: "objection",
    examples: ["150 nahi 200 ka hai ab", "Prices barh gaye hain bhai", "Old video lag rahi hai"],
    idea: "Show the date and receipt on screen. Do a 'prices then vs now' reel.",
  },
  {
    id: "th_05",
    theme: "Hygiene concerns",
    size: 64,
    dominant_label: "complaint",
    examples: ["Safai ka kya haal hai?", "Hands without gloves 😬", "Pani kaunsa use karte hain?"],
    idea: "Add a 10-second 'kitchen check' beat to street food reviews.",
  },
];

export const commentSummaryFixture: CommentSummary = {
  total: 1286,
  period_days: 30,
  by_label: [
    { label: "question", count: 452 },
    { label: "praise", count: 351 },
    { label: "request", count: 284 },
    { label: "objection", count: 104 },
    { label: "complaint", count: 69 },
    { label: "spam", count: 26 },
  ],
};

export const weeklyReportFixture: WeeklyReport = {
  week_start: "2026-10-13",
  headline: "Question hooks beat your median by 2.4×. Lean into them next week.",
  wins: [
    { title: "Samosa chaat price reveal", detail: "184K views, 3.4× your median. Variant C (stall owner opener) won the trial." },
    { title: "Saves up 47%", detail: "List and price-reveal formats drive saves. Viewers bookmark spots to visit." },
  ],
  losses: [
    { title: "Biryani bold claim", detail: "0.8× median. Bold claims underperform for your audience three weeks in a row." },
    { title: "Watch time down 6%", detail: "Reels over 40 s lose viewers at the 15 s mark. Tighten the middle beat." },
  ],
  themes: ["Where is this place?", "Try spots in other cities", "Prices seem wrong"],
  ideas: [
    { title: "Locations recap: 10 spots in 30 seconds", why: "412 comments asked for locations" },
    { title: "Karachi vs Lahore samosa chaat", why: "268 requests for other cities" },
    { title: "Prices then vs now at Anarkali", why: "Turns the price objection into content" },
    { title: "Honest rating: Lahore's most hyped nihari", why: "Praise theme + your best list format" },
    { title: "Kitchen check: street food hygiene", why: "Answers 64 hygiene complaints openly" },
  ],
};
