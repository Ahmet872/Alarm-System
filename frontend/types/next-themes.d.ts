declare module "next-themes" {
  import * as React from "react";

  interface ThemeProviderProps {
    attribute?: string;
    defaultTheme?: string;
    enableSystem?: boolean;
    children: React.ReactNode;
  }

  export const ThemeProvider: React.FC<ThemeProviderProps>;
  export function useTheme(): {
    theme: string | undefined;
    setTheme: (theme: string) => void;
    systemTheme: string | undefined;
  };
}