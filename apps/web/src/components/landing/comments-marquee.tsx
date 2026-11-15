import { cn } from "@/lib/utils";

import { SectionHeading, Soft } from "./section-heading";

/*
 * Two rows of cards moving in opposite directions with edge fades.
 * Adapted from the 21st.dev "Testimonials Marquee" (shadcnspace/marquee-01), rebuilt
 * on CSS keyframes so it needs no extra package. The cards hold example comments
 * with the label the classifier gives them, not customer testimonials.
 */

const LABELS = {
  question: { text: "Question", className: "bg-accent-soft text-accent" },
  request: { text: "Request", className: "bg-warning-soft text-warning" },
  praise: { text: "Praise", className: "bg-success-soft text-success" },
  complaint: { text: "Complaint", className: "bg-danger-soft text-danger" },
} as const;

type Comment = { name: string; handle: string; body: string; label: keyof typeof LABELS };

const ROW_ONE: Comment[] = [
  { name: "Ayesha", handle: "@ayesha.eats", body: "Ye kahan hai exact location? Next weekend jana hai 📍", label: "question" },
  { name: "Hamza", handle: "@hamza_k", body: "Karachi ka bhi review karo plz, Burns Road!", label: "request" },
  { name: "Sana", handle: "@sana.reviews", body: "Finally koi honest review deta hai ❤️", label: "praise" },
  { name: "Bilal", handle: "@bilal.lhr", body: "150 nahi 200 ka hai ab, update karo", label: "complaint" },
  { name: "Zoya", handle: "@zoyaaa", body: "Is this near Mall Road or Anarkali side?", label: "question" },
];

const ROW_TWO: Comment[] = [
  { name: "Usman", handle: "@usman.vlogs", body: "Islamabad aao kabhi, F-7 mein bhi try karo", label: "request" },
  { name: "Mahnoor", handle: "@mahnoor.m", body: "Your reactions are the best 😂 bohat acha content", label: "praise" },
  { name: "Ali", handle: "@ali_foodie", body: "Safai ka kya haal hai wahan? Honest batao", label: "question" },
  { name: "Fatima", handle: "@fatima.k", body: "Sound bohat low thi is video mein", label: "complaint" },
  { name: "Daniyal", handle: "@dani.eats", body: "Part 2 with desserts please 🙏", label: "request" },
];

function CommentCard({ comment }: { comment: Comment }) {
  const label = LABELS[comment.label];
  return (
    <li className="glass flex w-72 shrink-0 flex-col gap-3 rounded-2xl p-4">
      <div className="flex items-center gap-2.5">
        <span className="grid size-8 place-items-center rounded-full bg-surface-strong text-sm font-semibold">{comment.name[0]}</span>
        <span className="min-w-0 flex-1">
          <span className="block text-sm font-medium">{comment.name}</span>
          <span className="block text-xs text-subtle">{comment.handle}</span>
        </span>
        <span className={cn("rounded-pill px-2 py-0.5 text-[11px] font-semibold", label.className)}>{label.text}</span>
      </div>
      <p className="line-clamp-2 text-sm">{comment.body}</p>
    </li>
  );
}

function Marquee({ comments, reverse }: { comments: Comment[]; reverse?: boolean }) {
  return (
    <div className="flex overflow-hidden">
      <div
        className={cn(
          "flex animate-[marquee_40s_linear_infinite] gap-4 pr-4 hover:[animation-play-state:paused] motion-reduce:animate-none",
          reverse && "[animation-direction:reverse]",
        )}
      >
        <ul className="flex gap-4">
          {comments.map((comment) => (
            <CommentCard key={comment.handle} comment={comment} />
          ))}
        </ul>
        <ul aria-hidden className="flex gap-4">
          {comments.map((comment) => (
            <CommentCard key={comment.handle} comment={comment} />
          ))}
        </ul>
      </div>
    </div>
  );
}

export function CommentsMarquee() {
  return (
    <section className="py-20 sm:py-28">
      <SectionHeading
        className="px-4"
        title={
          <>
            Your comments, read properly.
            <br />
            <Soft>In the language they&apos;re written in.</Soft>
          </>
        }
      />
      <p className="mt-3 text-center text-[9.5px] font-extrabold tracking-[0.1em] text-subtle uppercase">Example comments</p>

      <div className="relative mt-12 space-y-4 py-2">
        <Marquee comments={ROW_ONE} />
        <Marquee comments={ROW_TWO} reverse />
        <div aria-hidden className="pointer-events-none absolute inset-y-0 left-0 w-1/5 bg-gradient-to-r from-canvas" />
        <div aria-hidden className="pointer-events-none absolute inset-y-0 right-0 w-1/5 bg-gradient-to-l from-canvas" />
      </div>
    </section>
  );
}
