import { Plus } from "lucide-react";

const FAQS = [
  {
    q: "Do I have to give you my Instagram password?",
    a: "No. You connect through Instagram's official login, and we only get the permissions you approve. Your password never reaches us.",
  },
  {
    q: "What are Trial Reels?",
    a: "An Instagram feature that shows a reel to people who don't follow you first. Reelmind posts each variant as a Trial Reel, so your followers only see the version that won.",
  },
  {
    q: "Who can join the pilot?",
    a: "Creators with a public professional Instagram account, 1,000+ followers, and a few reels a week. Trial Reels need a public account with at least 1,000 followers.",
  },
  {
    q: "Which languages does it support?",
    a: "English, Urdu and Roman Urdu, including both mixed in one sentence, for scripts, captions and comment analysis.",
  },
  {
    q: "Do you download other creators' reels?",
    a: "No. You upload the reference reels you want broken down. We never scrape other accounts.",
  },
  {
    q: "Can I delete my data?",
    a: "Yes. Disconnect Instagram and delete everything, videos and comments included, from settings at any time.",
  },
];

/** Native <details> accordion: accessible and keyboard friendly with no script. */
export function FaqSection() {
  return (
    <section id="faq" className="scroll-mt-10 px-4 py-20 sm:px-6 sm:py-28">
      <div className="mx-auto grid max-w-[1180px] gap-10 lg:grid-cols-[1fr_1.4fr]">
        <h2 className="reveal text-[clamp(2.125rem,5vw,4rem)] leading-[1.02] font-semibold tracking-[-0.045em]">
          Common
          <br />
          questions
        </h2>

        <div className="reveal glass divide-y divide-edge rounded-3xl px-6">
          {FAQS.map((faq) => (
            <details key={faq.q} className="group py-5">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-4 text-[15.5px] font-medium [&::-webkit-details-marker]:hidden">
                {faq.q}
                <Plus aria-hidden className="size-4 shrink-0 text-subtle transition-transform group-open:rotate-45" />
              </summary>
              <p className="mt-3 max-w-xl text-[15px] leading-[1.55] text-muted">{faq.a}</p>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}
