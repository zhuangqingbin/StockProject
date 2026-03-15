import { useEffect, useRef, useState } from "react";

export const useScrollActivatedVisibility = <T extends HTMLElement>() => {
  const containerRef = useRef<T | null>(null);
  const [hasScrolled, setHasScrolled] = useState(() =>
    typeof window !== "undefined" ? window.scrollY > 0 : false,
  );
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") {
      return undefined;
    }

    const markScrolled = () => {
      if (window.scrollY > 0) {
        setHasScrolled(true);
      }
    };

    markScrolled();
    window.addEventListener("scroll", markScrolled, { passive: true });
    return () => window.removeEventListener("scroll", markScrolled);
  }, []);

  useEffect(() => {
    const node = containerRef.current;
    if (!node) {
      return undefined;
    }

    if (typeof IntersectionObserver === "undefined") {
      setIsVisible(true);
      return undefined;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        setIsVisible(entries.some((entry) => entry.isIntersecting));
      },
      { rootMargin: "120px 0px" },
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return {
    containerRef,
    trendReady: hasScrolled && isVisible,
  };
};
