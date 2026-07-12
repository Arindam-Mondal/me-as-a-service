/* Display copy for the profile panel. Kept in sync with content/about.md, but this is
   the visual/marketing layer — the chat answers are grounded server-side. */

export type Social = { kind: "github" | "linkedin"; href: string; label: string };

export const profile = {
  name: "Arindam Mondal",
  initials: "AM",
  headline: "Lead Full Stack Developer · building agentic AI & RAG",
  avatar: "/avatar.jpg", // owner to supply; falls back to initials in a doodle ring
  bio: "I am a Lead AI/ML Engineer at FICO with over 12 years of experience shipping enterprise-grade platforms. Building multi-purpose next-gen systems, treat me as your technical co-pilot—I only know what I've been told about our tech stack, platform architecture, and industry standards.",
  socials: [
    { kind: "github", href: "https://github.com/Arindam-Mondal", label: "GitHub" },
    { kind: "linkedin", href: "https://linkedin.com/in/amond", label: "LinkedIn" },
  ] as Social[],
  starters: [
    "What are Arindam's skills?",
    "What is he building at FICO?",
    "Tell me about the Cougar low-code framework.",
    "What is he looking for next?",
  ],
} as const;
