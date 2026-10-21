import {
  Clapperboard,
  Dna,
  FileChartColumn,
  FlaskConical,
  LayoutDashboard,
  MessagesSquare,
  PenLine,
  type LucideIcon,
} from "lucide-react";

export type NavItem = { href: string; label: string; icon: LucideIcon };

export const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dna", label: "DNA library", icon: Dna },
  { href: "/studio", label: "Script studio", icon: PenLine },
  { href: "/editor", label: "Editor", icon: Clapperboard },
  { href: "/variants", label: "Variants", icon: FlaskConical },
  { href: "/comments", label: "Comments", icon: MessagesSquare },
  { href: "/reports", label: "Weekly report", icon: FileChartColumn },
];

export const APP_NAME = "Reelmind";
