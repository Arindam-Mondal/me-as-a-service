/* Display copy for the profile panel. Kept in sync with content/about.md, but this is
   the visual/marketing layer — the chat answers are grounded server-side. */

export type Social = { kind: "github" | "linkedin"; href: string; label: string };

export const profile = {
  name: "Arindam Mondal",
  initials: "AM",
  headline: "Lead Full Stack Developer · building agentic AI & RAG",
  avatar: "/avatar.jpg", // owner to supply; falls back to initials in a doodle ring
  bio: "I'm a Lead Engineer at FICO with over 12 years of experience shipping enterprise-grade platforms, with a full-stack background across the stack. Currently building Agentic AI capabilities and RAG systems for next-gen, multi-purpose platforms.",
  bioHighlights: ["Agentic AI", "RAG"], // terms given the marker-swipe highlight in ProfilePanel
  socials: [
    { kind: "github", href: "https://github.com/Arindam-Mondal", label: "GitHub" },
    { kind: "linkedin", href: "https://linkedin.com/in/amond", label: "LinkedIn" },
  ] as Social[],
  starters: [
    "What are Arindam's skills?",
    "What is he building at FICO?",
    "What impact has he made in his work?",
    "What is he looking for next?",
  ],
} as const;
