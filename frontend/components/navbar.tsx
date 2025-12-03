"use client";
import { cn } from "@/lib/utils";
import { IconMenu2, IconX, IconSparkles, IconUser, IconLogout, IconChevronDown } from "@tabler/icons-react";
import {
  motion,
  AnimatePresence,
  useScroll,
  useMotionValueEvent,
} from "motion/react";
import Link from "next/link";
import React, { useRef, useState } from "react";
import { Button } from "./button";
import { Logo } from "./logo";
import { useChatContext } from "./chat-provider";
import { useAuth } from "@/lib/auth/context";
import { useWatchlist } from "@/lib/hooks/useWatchlist";

interface NavItem {
  name: string;
  link?: string;
  dropdown?: { name: string; link: string; icon?: string }[];
}

interface NavbarProps {
  navItems: NavItem[];
  visible: boolean;
}

export const Navbar = () => {
  // Consolidated navigation - 5 primary items
  const navItems: NavItem[] = [
    {
      name: "Dashboard",
      link: "/dashboard",
    },
    {
      name: "Explore",
      dropdown: [
        { name: "Targets", link: "/explore/targets", icon: "🎯" },
        { name: "Drugs", link: "/explore/drugs", icon: "💊" },
        { name: "Companies", link: "/explore/companies", icon: "🏢" },
        { name: "Editing Assets", link: "/explore/editing", icon: "🧬" },
        { name: "Combos", link: "/explore/combos", icon: "🔗" },
        { name: "Patents", link: "/explore/patents", icon: "📜" },
      ],
    },
    {
      name: "News",
      link: "/explore/news",
    },
    {
      name: "Calendar",
      link: "/calendar",
    },
    {
      name: "Watchlist",
      link: "/watchlist",
    },
  ];

  const ref = useRef<HTMLDivElement>(null);
  const { scrollY } = useScroll({
    target: ref,
    offset: ["start start", "end start"],
  });
  const [visible, setVisible] = useState<boolean>(false);

  useMotionValueEvent(scrollY, "change", (latest) => {
    if (latest > 100) {
      setVisible(true);
    } else {
      setVisible(false);
    }
  });

  return (
    <motion.div
      ref={ref}
      className="w-full sticky top-2 inset-x-0 z-50"
      suppressHydrationWarning
    >
      <DesktopNav visible={visible} navItems={navItems} />
      <MobileNav visible={visible} navItems={navItems} />
    </motion.div>
  );
};

const DesktopNav = ({ navItems, visible }: NavbarProps) => {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [activeDropdown, setActiveDropdown] = useState<number | null>(null);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const { openChat } = useChatContext();
  const { user, profile, loading: authLoading, signOut } = useAuth();
  const { items: watchlistItems } = useWatchlist();

  return (
    <motion.div
      onMouseLeave={() => {
        setHoveredIndex(null);
        setActiveDropdown(null);
      }}
      animate={{
        backdropFilter: "blur(16px)",
        background: visible ? "rgba(0, 0, 0, 0.7)" : "rgba(0, 0, 0, 0.4)",
        width: visible ? "60%" : "80%",
        height: visible ? "48px" : "64px",
        y: visible ? 8 : 0,
      }}
      initial={{
        width: "80%",
        height: "64px",
        background: "rgba(0, 0, 0, 0.4)",
      }}
      transition={{
        type: "spring",
        stiffness: 400,
        damping: 30,
      }}
      className={cn(
        "hidden lg:flex flex-row self-center items-center justify-between py-2 mx-auto px-6 rounded-full relative z-[60] backdrop-saturate-[1.8]"
      )}
    >
      <Logo />
      <motion.div
        className="lg:flex flex-row flex-1 items-center justify-center space-x-1 text-sm"
        animate={{
          scale: visible ? 0.95 : 1,
          justifyContent: visible ? "flex-end" : "center",
        }}
      >
        {navItems.map((navItem, idx) => (
          <motion.div
            key={`nav-item-${idx}`}
            onHoverStart={() => {
              setHoveredIndex(idx);
              if (navItem.dropdown) {
                setActiveDropdown(idx);
              }
            }}
            onHoverEnd={() => {
              if (!navItem.dropdown) {
                setHoveredIndex(null);
              }
            }}
            className="relative"
          >
            {navItem.dropdown ? (
              // Dropdown menu item
              <button
                className="text-white/90 relative px-3 py-1.5 transition-colors flex items-center gap-1"
                onClick={() => setActiveDropdown(activeDropdown === idx ? null : idx)}
              >
                <span className="relative z-10">{navItem.name}</span>
                <IconChevronDown className={cn(
                  "w-3.5 h-3.5 transition-transform",
                  activeDropdown === idx && "rotate-180"
                )} />
                {hoveredIndex === idx && (
                  <motion.div
                    layoutId="menu-hover"
                    className="absolute inset-0 rounded-full bg-gradient-to-r from-white/10 to-white/20"
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{
                      opacity: 1,
                      scale: 1.1,
                      background:
                        "radial-gradient(circle at center, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0.1) 50%, transparent 100%)",
                    }}
                    exit={{ opacity: 0, scale: 0.8 }}
                    transition={{ type: "spring", bounce: 0.4, duration: 0.4 }}
                  />
                )}
              </button>
            ) : (
              // Regular link
              <Link
                className="text-white/90 relative px-3 py-1.5 transition-colors flex items-center gap-1"
                href={navItem.link || "/"}
              >
                <span className="relative z-10">{navItem.name}</span>
                {/* Watchlist badge */}
                {navItem.name === "Watchlist" && watchlistItems.length > 0 && (
                  <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-pd-accent text-white text-[10px] font-bold flex items-center justify-center">
                    {watchlistItems.length > 9 ? "9+" : watchlistItems.length}
                  </span>
                )}
                {hoveredIndex === idx && (
                  <motion.div
                    layoutId="menu-hover"
                    className="absolute inset-0 rounded-full bg-gradient-to-r from-white/10 to-white/20"
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{
                      opacity: 1,
                      scale: 1.1,
                      background:
                        "radial-gradient(circle at center, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0.1) 50%, transparent 100%)",
                    }}
                    exit={{ opacity: 0, scale: 0.8 }}
                    transition={{ type: "spring", bounce: 0.4, duration: 0.4 }}
                  />
                )}
              </Link>
            )}

            {/* Dropdown panel */}
            <AnimatePresence>
              {navItem.dropdown && activeDropdown === idx && (
                <motion.div
                  initial={{ opacity: 0, y: -10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -10, scale: 0.95 }}
                  transition={{ duration: 0.15 }}
                  className="absolute left-0 top-full mt-2 w-48 py-2 rounded-xl bg-black/95 backdrop-blur-xl border border-white/20 shadow-xl z-[100]"
                  onMouseEnter={() => setActiveDropdown(idx)}
                  onMouseLeave={() => {
                    setActiveDropdown(null);
                    setHoveredIndex(null);
                  }}
                >
                  {navItem.dropdown.map((item, dropIdx) => (
                    <Link
                      key={dropIdx}
                      href={item.link}
                      className="flex items-center gap-2 px-4 py-2 text-sm text-white/80 hover:text-white hover:bg-white/10 transition-colors"
                      onClick={() => setActiveDropdown(null)}
                    >
                      {item.icon && <span>{item.icon}</span>}
                      {item.name}
                    </Link>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </motion.div>
      <div className="flex items-center gap-2">
        <button
          onClick={openChat}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gradient-to-r from-blue-600/20 to-blue-500/10 border border-blue-500/30 hover:border-blue-400/50 text-blue-400 hover:text-blue-300 transition-all text-sm whitespace-nowrap leading-none min-w-[82px]"
        >
          <IconSparkles className="w-4 h-4" />
          <span>Ask AI</span>
        </button>
        <AnimatePresence mode="popLayout" initial={false}>
          {!visible && !user && (
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{
                scale: 1,
                opacity: 1,
                transition: {
                  type: "spring",
                  stiffness: 400,
                  damping: 25,
                },
              }}
              exit={{
                scale: 0.8,
                opacity: 0,
                transition: {
                  duration: 0.2,
                },
              }}
            >
              <Button
                as={Link}
                href="/login"
                variant="primary"
                className="hidden md:block rounded-full bg-white/20 hover:bg-white/30 text-white border-0"
              >
                Sign In
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
        {/* User Menu - Show when logged in */}
        {!authLoading && user && (
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 hover:bg-white/20 text-white transition-all text-sm"
            >
              <IconUser className="w-4 h-4" />
              <span className="hidden xl:inline max-w-[100px] truncate">
                {profile?.full_name || user.email?.split("@")[0] || "Account"}
              </span>
            </button>
            <AnimatePresence>
              {showUserMenu && (
                <motion.div
                  initial={{ opacity: 0, y: -10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -10, scale: 0.95 }}
                  transition={{ duration: 0.15 }}
                  className="absolute right-0 top-full mt-2 w-56 py-2 rounded-xl bg-black/90 backdrop-blur-xl border border-white/20 shadow-xl z-[100]"
                  onMouseLeave={() => setShowUserMenu(false)}
                >
                  <div className="px-4 py-2 border-b border-white/10">
                    <div className="text-sm text-white truncate">
                      {user.email}
                    </div>
                    <div className="text-xs text-white/50 mt-0.5 flex items-center gap-1">
                      <span className={cn(
                        "inline-block w-2 h-2 rounded-full",
                        profile?.subscription_tier === "enterprise" ? "bg-purple-500" :
                        profile?.subscription_tier === "pro" ? "bg-blue-500" : "bg-gray-500"
                      )} />
                      {profile?.subscription_tier === "enterprise" ? "Enterprise" :
                       profile?.subscription_tier === "pro" ? "Pro" : "Free"} Plan
                    </div>
                  </div>
                  <div className="py-1">
                    <Link
                      href="/dashboard"
                      className="flex items-center gap-2 px-4 py-2 text-sm text-white/80 hover:text-white hover:bg-white/10 transition-colors"
                      onClick={() => setShowUserMenu(false)}
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                      </svg>
                      My Dashboard
                    </Link>
                    <Link
                      href="/watchlist"
                      className="flex items-center gap-2 px-4 py-2 text-sm text-white/80 hover:text-white hover:bg-white/10 transition-colors"
                      onClick={() => setShowUserMenu(false)}
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                      My Watchlist
                      {watchlistItems.length > 0 && (
                        <span className="ml-auto text-xs bg-pd-accent/20 text-pd-accent px-1.5 py-0.5 rounded">
                          {watchlistItems.length}
                        </span>
                      )}
                    </Link>
                    <Link
                      href="/settings/billing"
                      className="flex items-center gap-2 px-4 py-2 text-sm text-white/80 hover:text-white hover:bg-white/10 transition-colors"
                      onClick={() => setShowUserMenu(false)}
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      Settings & Billing
                    </Link>
                  </div>
                  <div className="border-t border-white/10 pt-1">
                    <button
                      onClick={async () => {
                        setShowUserMenu(false);
                        await signOut();
                      }}
                      className="flex items-center gap-2 w-full px-4 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors"
                    >
                      <IconLogout className="w-4 h-4" />
                      Sign Out
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}
        {/* Login Button - Show when not logged in */}
        {!authLoading && !user && visible && (
          <Link
            href="/login"
            className="px-3 py-1.5 rounded-full bg-white/10 hover:bg-white/20 text-white text-sm transition-all"
          >
            Sign In
          </Link>
        )}
      </div>
    </motion.div>
  );
};

const MobileNav = ({ navItems, visible }: NavbarProps) => {
  const [open, setOpen] = useState(false);
  const [expandedDropdown, setExpandedDropdown] = useState<number | null>(null);
  const { openChat } = useChatContext();
  const { user, loading: authLoading, signOut } = useAuth();
  const { items: watchlistItems } = useWatchlist();

  return (
    <>
      <motion.div
        animate={{
          backdropFilter: "blur(16px)",
          background: visible ? "rgba(0, 0, 0, 0.7)" : "rgba(0, 0, 0, 0.4)",
          width: visible ? "80%" : "90%",
          y: visible ? 0 : 8,
          borderRadius: open ? "24px" : "999px",
          padding: "8px 16px",
        }}
        initial={{
          width: "80%",
          background: "rgba(0, 0, 0, 0.4)",
        }}
        transition={{
          type: "spring",
          stiffness: 400,
          damping: 30,
        }}
        className={cn(
          "flex relative flex-col lg:hidden w-full justify-between items-center max-w-[calc(100vw-2rem)] mx-auto z-50 backdrop-saturate-[1.8] border border-solid border-white/40 rounded-full"
        )}
      >
        <div className="flex flex-row justify-between items-center w-full">
          <Logo />
          <div className="flex items-center gap-3">
            <button
              onClick={openChat}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-full bg-gradient-to-r from-blue-600/20 to-blue-500/10 border border-blue-500/30 text-blue-400 text-sm"
            >
              <IconSparkles className="w-4 h-4" />
              <span>AI</span>
            </button>
            {open ? (
              <IconX className="text-white/90" onClick={() => setOpen(!open)} />
            ) : (
              <IconMenu2
                className="text-white/90"
                onClick={() => setOpen(!open)}
              />
            )}
          </div>
        </div>

        <AnimatePresence>
          {open && (
            <motion.div
              initial={{
                opacity: 0,
                y: -20,
              }}
              animate={{
                opacity: 1,
                y: 0,
              }}
              exit={{
                opacity: 0,
                y: -20,
              }}
              transition={{
                type: "spring",
                stiffness: 400,
                damping: 30,
              }}
              className="flex rounded-3xl absolute top-16 bg-black/80 backdrop-blur-xl backdrop-saturate-[1.8] inset-x-0 z-50 flex-col items-start justify-start gap-2 w-full px-6 py-6"
            >
              {navItems.map((navItem, idx) => (
                <div key={`mobile-nav-${idx}`} className="w-full">
                  {navItem.dropdown ? (
                    // Dropdown in mobile
                    <>
                      <button
                        onClick={() => setExpandedDropdown(expandedDropdown === idx ? null : idx)}
                        className="flex items-center justify-between w-full text-white/90 hover:text-white transition-colors py-2"
                      >
                        <span>{navItem.name}</span>
                        <IconChevronDown className={cn(
                          "w-4 h-4 transition-transform",
                          expandedDropdown === idx && "rotate-180"
                        )} />
                      </button>
                      <AnimatePresence>
                        {expandedDropdown === idx && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-hidden pl-4 border-l border-white/20 ml-2"
                          >
                            {navItem.dropdown.map((item, dropIdx) => (
                              <Link
                                key={dropIdx}
                                href={item.link}
                                onClick={() => setOpen(false)}
                                className="flex items-center gap-2 py-2 text-white/70 hover:text-white transition-colors"
                              >
                                {item.icon && <span>{item.icon}</span>}
                                {item.name}
                              </Link>
                            ))}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </>
                  ) : (
                    // Regular link in mobile
                    <Link
                      href={navItem.link || "/"}
                      onClick={() => setOpen(false)}
                      className="flex items-center gap-2 w-full text-white/90 hover:text-white transition-colors py-2"
                    >
                      <span>{navItem.name}</span>
                      {navItem.name === "Watchlist" && watchlistItems.length > 0 && (
                        <span className="ml-auto text-xs bg-pd-accent/20 text-pd-accent px-1.5 py-0.5 rounded">
                          {watchlistItems.length}
                        </span>
                      )}
                    </Link>
                  )}
                </div>
              ))}
              {/* Auth section in mobile menu */}
              <div className="w-full pt-4 border-t border-white/20">
                {!authLoading && user ? (
                  <div className="space-y-3">
                    <div className="text-xs text-white/50 flex items-center gap-2">
                      <IconUser className="w-4 h-4" />
                      <span className="truncate">{user.email}</span>
                    </div>
                    <Link
                      href="/dashboard"
                      onClick={() => setOpen(false)}
                      className="block text-white/90 hover:text-white transition-colors"
                    >
                      My Dashboard
                    </Link>
                    <Link
                      href="/settings/billing"
                      onClick={() => setOpen(false)}
                      className="block text-white/90 hover:text-white transition-colors"
                    >
                      Settings & Billing
                    </Link>
                    <button
                      onClick={async () => {
                        setOpen(false);
                        await signOut();
                      }}
                      className="flex items-center gap-2 text-red-400 hover:text-red-300 transition-colors"
                    >
                      <IconLogout className="w-4 h-4" />
                      Sign Out
                    </button>
                  </div>
                ) : (
                  <div className="flex gap-3">
                    <Link
                      href="/login"
                      onClick={() => setOpen(false)}
                      className="flex-1 text-center py-2 rounded-lg bg-white/10 text-white font-medium"
                    >
                      Sign In
                    </Link>
                    <Link
                      href="/signup"
                      onClick={() => setOpen(false)}
                      className="flex-1 text-center py-2 rounded-lg bg-pd-accent text-white font-medium"
                    >
                      Sign Up
                    </Link>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </>
  );
};
