import { useColorMode } from "@vueuse/core"

export const useTheme = () => {
  const mode = useColorMode({
    attribute: "class",
    modes: { light: "light", dark: "dark" }
  })
  const toggle = () => {
    mode.value = mode.value === "dark" ? "light" : "dark"
  }
  return { mode, toggle }
}
