"use client";

import React from "react";
import { motion, HTMLMotionProps } from "framer-motion";

interface GlassCardProps extends HTMLMotionProps<"div"> {
  children: React.ReactNode;
  className?: string;
  interactive?: boolean;
}

export default function GlassCard({
  children,
  className = "",
  interactive = false,
  ...props
}: GlassCardProps) {
  return (
    <motion.div
      className={`glass-card ${interactive ? "glass-card-interactive" : ""} ${className}`}
      {...props}
    >
      {children}
    </motion.div>
  );
}
