import { createPortal } from "react-dom";
import type { ChangeEvent, KeyboardEventHandler, MouseEventHandler, ReactNode } from "react";

type Tone = "info" | "warning" | "error";

const joinClasses = (...parts: Array<string | false | null | undefined>) =>
  parts.filter(Boolean).join(" ");

export const Surface = ({
  className,
  children,
}: {
  className?: string;
  children: ReactNode;
}) => <section className={joinClasses("ui-surface", className)}>{children}</section>;

export const Button = ({
  children,
  onClick,
  loading = false,
  disabled = false,
  variant = "primary",
  size = "md",
  className,
  type = "button",
}: {
  children: ReactNode;
  onClick?: MouseEventHandler<HTMLButtonElement>;
  loading?: boolean;
  disabled?: boolean;
  variant?: "primary" | "ghost";
  size?: "sm" | "md";
  className?: string;
  type?: "button" | "submit";
}) => (
  <button
    type={type}
    className={joinClasses("ui-button", `ui-button--${variant}`, `ui-button--${size}`, className)}
    onClick={onClick}
    disabled={disabled || loading}
  >
    {loading ? "处理中..." : children}
  </button>
);

export const StatusBadge = ({
  label,
  status,
}: {
  label: string;
  status: "connecting" | "connected" | "disconnected";
}) => (
  <span className={joinClasses("ui-status", `ui-status--${status}`)}>
    <span className="ui-status__dot" aria-hidden="true" />
    {label}
  </span>
);

export const AlertBanner = ({
  title,
  description,
  tone = "info",
  onClose,
  className,
}: {
  title: string;
  description?: string | null;
  tone?: Tone;
  onClose?: () => void;
  className?: string;
}) => (
  <div className={joinClasses("ui-alert", `ui-alert--${tone}`, className)}>
    <div className="ui-alert__body">
      <strong className="ui-alert__title">{title}</strong>
      {description ? <p className="ui-alert__description">{description}</p> : null}
    </div>
    {onClose ? (
      <button className="ui-alert__close" onClick={onClose} aria-label="关闭提示">
        ×
      </button>
    ) : null}
  </div>
);

export const EmptyState = ({
  title = "暂无数据",
  description,
  action,
}: {
  title?: string;
  description?: string;
  action?: ReactNode;
}) => (
  <div className="ui-empty">
    <div className="ui-empty__icon" aria-hidden="true">
      ∅
    </div>
    <strong className="ui-empty__title">{title}</strong>
    {description ? <p className="ui-empty__description">{description}</p> : null}
    {action ? <div className="ui-empty__action">{action}</div> : null}
  </div>
);

export const LoadingBlock = ({ rows = 5 }: { rows?: number }) => (
  <div className="ui-loading" aria-label="loading">
    {Array.from({ length: rows }, (_, index) => (
      <span key={index} className="ui-loading__row" />
    ))}
  </div>
);

export const MetricTile = ({
  label,
  value,
  suffix,
}: {
  label: string;
  value: ReactNode;
  suffix?: ReactNode;
}) => (
  <div className="ui-metric">
    <span className="ui-metric__label">{label}</span>
    <strong className="ui-metric__value">
      {value}
      {suffix ? <span className="ui-metric__suffix">{suffix}</span> : null}
    </strong>
  </div>
);

export const SegmentedControl = <T extends string>({
  value,
  onChange,
  options,
}: {
  value: T;
  onChange: (value: T) => void;
  options: Array<{ label: string; value: T }>;
}) => (
  <div className="ui-segmented" role="tablist">
    {options.map((option) => (
      <button
        key={option.value}
        type="button"
        className={joinClasses("ui-segmented__item", option.value === value && "is-active")}
        onClick={() => onChange(option.value)}
      >
        {option.label}
      </button>
    ))}
  </div>
);

export const SelectField = <T extends string | number>({
  value,
  onChange,
  options,
  minWidth,
}: {
  value: T;
  onChange: (value: T) => void;
  options: Array<{ label: string; value: T }>;
  minWidth?: number;
}) => (
  <label className="ui-select" style={minWidth ? { minWidth } : undefined}>
    <select
      value={String(value)}
      onChange={(event: ChangeEvent<HTMLSelectElement>) =>
        onChange(options.find((option) => String(option.value) === event.target.value)?.value ?? value)
      }
    >
      {options.map((option) => (
        <option key={option.label} value={String(option.value)}>
          {option.label}
        </option>
      ))}
    </select>
  </label>
);

export const TextAreaField = ({
  value,
  onChange,
  onKeyDown,
  placeholder,
  rows = 4,
}: {
  value: string;
  onChange: (value: string) => void;
  onKeyDown?: KeyboardEventHandler<HTMLTextAreaElement>;
  placeholder?: string;
  rows?: number;
}) => (
  <label className="ui-textarea">
    <textarea
      value={value}
      rows={rows}
      placeholder={placeholder}
      onChange={(event) => onChange(event.target.value)}
      onKeyDown={onKeyDown}
    />
  </label>
);

export const DescriptionGrid = ({
  items,
  columns = 3,
}: {
  items: Array<{ label: string; value: ReactNode }>;
  columns?: 2 | 3;
}) => (
  <dl className={joinClasses("ui-description-grid", `ui-description-grid--${columns}`)}>
    {items.map((item) => (
      <div key={item.label} className="ui-description-grid__item">
        <dt>{item.label}</dt>
        <dd>{item.value}</dd>
      </div>
    ))}
  </dl>
);

type Column<T> = {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
};

export const DataTable = <T,>({
  data,
  columns,
  rowKey,
  onRowClick,
}: {
  data: T[];
  columns: Array<Column<T>>;
  rowKey: (row: T) => string;
  onRowClick?: (row: T) => void;
}) => (
  <div className="ui-table-wrap">
    <table className="ui-table">
      <thead>
        <tr>
          {columns.map((column) => (
            <th key={column.key}>{column.header}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.map((row) => (
          <tr
            key={rowKey(row)}
            className={onRowClick ? "is-clickable" : undefined}
            onClick={() => onRowClick?.(row)}
          >
            {columns.map((column) => (
              <td key={column.key}>{column.render(row)}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

export const DrawerPanel = ({
  open,
  title,
  width = 920,
  onClose,
  children,
}: {
  open: boolean;
  title: string;
  width?: number;
  onClose: () => void;
  children: ReactNode;
}) => {
  if (!open || typeof document === "undefined") {
    return null;
  }

  return createPortal(
    <div className="ui-drawer-layer" role="dialog" aria-modal="true">
      <button className="ui-drawer-layer__backdrop" onClick={onClose} aria-label="关闭抽屉" />
      <aside className="ui-drawer" style={{ width }}>
        <header className="ui-drawer__header">
          <h2>{title}</h2>
          <button className="ui-drawer__close" onClick={onClose} aria-label="关闭">
            ×
          </button>
        </header>
        <div className="ui-drawer__body">{children}</div>
      </aside>
    </div>,
    document.body,
  );
};
