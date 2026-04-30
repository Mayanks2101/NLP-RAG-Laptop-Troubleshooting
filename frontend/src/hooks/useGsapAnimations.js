import { useEffect } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

/**
 * Staggered fade+slideX animation for sidebar items.
 */
export function useSidebarAnimation(containerRef, deps = []) {
  useEffect(() => {
    if (!containerRef.current) return;
    const items = containerRef.current.querySelectorAll('.sidebar-chat-item');
    if (items.length === 0) return;

    gsap.fromTo(
      items,
      { opacity: 0, x: -20 },
      {
        opacity: 1,
        x: 0,
        duration: 0.35,
        stagger: 0.04,
        ease: 'power2.out',
        clearProps: 'transform',
      }
    );
  }, deps);
}

/**
 * Fade-in + slideY for a single message bubble.
 */
export function useMessageAnimation(ref) {
  useEffect(() => {
    if (!ref.current) return;
    // Animate immediately on mount — no ScrollTrigger so it always fires
    // (ScrollTrigger could miss newly-appended messages and leave them at opacity:0)
    gsap.fromTo(
      ref.current,
      { opacity: 0, y: 25 },
      {
        opacity: 1,
        y: 0,
        duration: 0.45,
        ease: 'power3.out',
      }
    );
  }, [ref]);
}

/**
 * Staggered fade+slideY animation for the empty state hero section.
 */
export function useHeroAnimation(ref) {
  useEffect(() => {
    if (!ref.current) return;
    const elements = ref.current.children;
    gsap.fromTo(
      elements,
      { opacity: 0, y: 30 },
      {
        opacity: 1,
        y: 0,
        duration: 0.6,
        stagger: 0.15,
        ease: 'power3.out',
      }
    );
  }, [ref]);
}

/**
 * Slide debug panel in/out from the right.
 */
export function useDebugPanelAnimation(ref, isOpen) {
  useEffect(() => {
    if (!ref.current) return;
    if (isOpen) {
      gsap.fromTo(
        ref.current,
        { x: '100%', opacity: 0 },
        { x: '0%', opacity: 1, duration: 0.45, ease: 'power3.out' }
      );
    } else {
      gsap.to(ref.current, {
        x: '100%',
        opacity: 0,
        duration: 0.3,
        ease: 'power3.in',
      });
    }
  }, [isOpen]);
}
