import * as React from "react"
import { cn } from "../../lib/utils"

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'outline' | 'ghost' | 'link' | 'destructive'
  size?: 'default' | 'sm' | 'lg' | 'icon'
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', ...props }, ref) => {
    
    const variants = {
      default: "bg-primary-main text-white hover:bg-primary-hover shadow-soft",
      destructive: "bg-red-500 text-white hover:bg-red-600 shadow-soft",
      outline: "border border-primary-light bg-transparent hover:bg-primary-light/50 text-primary-main",
      ghost: "hover:bg-primary-light/50 text-primary-main",
      link: "text-primary-main underline-offset-4 hover:underline",
    }
    
    const sizes = {
      default: "min-h-[44px] h-[44px] sm:h-10 px-4 py-2",
      sm: "min-h-[44px] h-[44px] sm:h-9 rounded-md px-3",
      lg: "min-h-[44px] h-[44px] sm:h-11 rounded-md px-8 text-lg",
      icon: "min-h-[44px] h-[44px] sm:h-10 w-[44px] sm:w-10",
    }

    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center whitespace-nowrap rounded-xl text-sm font-medium ring-offset-background transition-[transform,background-color,border-color,color] duration-150 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-main disabled:pointer-events-none disabled:opacity-50 active:scale-[0.97]",
          variants[variant],
          sizes[size],
          className
        )}
        onClick={(e) => {
          if (typeof navigator !== 'undefined' && navigator.vibrate) {
            navigator.vibrate([15]); // Subtle haptic feedback
          }
          if (props.onClick) {
            props.onClick(e);
          }
        }}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button }
