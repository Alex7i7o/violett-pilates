/* Developed by FireSeed - Fueling Innovation */
import * as React from "react"
import { cn } from "../../lib/utils"

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'secondary' | 'outline' | 'success' | 'destructive'
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  
  const variants = {
    default: "bg-violett-900 text-white shadow hover:bg-violett-800",
    secondary: "bg-violett-100 text-violett-900 hover:bg-violett-200",
    outline: "text-foreground border border-violett-200",
    success: "bg-green-100 text-green-800 border-green-200",
    destructive: "bg-red-100 text-red-800 border-red-200",
  }
  
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-violett-500 focus:ring-offset-2",
        variants[variant],
        className
      )}
      {...props}
    />
  )
}

export { Badge }
