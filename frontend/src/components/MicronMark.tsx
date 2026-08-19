import type { FC, ImgHTMLAttributes } from "react";
import micronWordmark from "../assets/micron-wordmark.png";

/**
 * Real Micron wordmark (black ink, transparent background). Renders as an
 * <img> rather than inline SVG since it's a raster asset - size via
 * className height utilities (e.g. h-6) and let width follow naturally.
 */
export const MicronMark: FC<ImgHTMLAttributes<HTMLImageElement>> = ({ className, ...props }) => (
  <img src={micronWordmark} alt="Micron" className={className} {...props} />
);
