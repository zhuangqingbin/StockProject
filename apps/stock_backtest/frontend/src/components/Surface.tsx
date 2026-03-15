import type { PropsWithChildren, ReactNode } from "react";

type SurfaceProps = PropsWithChildren<{
  title?: string;
  eyebrow?: string;
  action?: ReactNode;
  className?: string;
}>;

export const Surface = ({ title, eyebrow, action, className, children }: SurfaceProps) => (
  <section className={`surface ${className ?? ""}`.trim()}>
    {(title || eyebrow || action) && (
      <div className="surface__header">
        <div>
          {eyebrow ? <p className="surface__eyebrow">{eyebrow}</p> : null}
          {title ? <h2 className="surface__title">{title}</h2> : null}
        </div>
        {action ? <div>{action}</div> : null}
      </div>
    )}
    {children}
  </section>
);
