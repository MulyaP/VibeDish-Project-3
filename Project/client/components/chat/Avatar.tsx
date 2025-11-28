"use client"

import React from "react"

export default function Avatar({ name, size = 40 }: { name: string; size?: number }) {
  const initials = name
    .split(" ")
    .map((p) => p.charAt(0))
    .slice(0, 2)
    .join("")
    .toUpperCase()

  const style: React.CSSProperties = {
    width: size,
    height: size,
  }

  return (
    <div
      className="flex items-center justify-center rounded-full bg-gray-200 text-gray-800 font-semibold"
      style={style}
      aria-hidden="true"
    >
      {initials}
    </div>
  )
}
