import { useId, useState, type ReactNode } from "react";

type ButtonProps = {
  children: ReactNode;
  onClick?: () => void;
  type?: "button" | "submit" | "reset";
  variant?: "primary" | "secondary";
  size?: "default" | "large";
};

type StatusTagProps = {
  children: ReactNode;
  tone?: "accent" | "positive" | "warning" | "negative" | "neutral";
};

type ProgressBarProps = {
  value: number;
};

type ColumnDefinition<T> = {
  key: string;
  title: ReactNode;
  dataIndex?: keyof T;
  render?: (record: T) => ReactNode;
};

type DataTableProps<T> = {
  columns: ColumnDefinition<T>[];
  data: T[];
  rowKey: keyof T | ((record: T) => string | number);
};

type TabItem = {
  key: string;
  label: ReactNode;
  children: ReactNode;
};

type TabsProps = {
  items: TabItem[];
  defaultActiveKey?: string;
};

const buttonClassMap = {
  primary: "ui-button ui-button--primary",
  secondary: "ui-button ui-button--secondary",
} as const;

const buttonSizeClassMap = {
  default: "",
  large: " ui-button--large",
} as const;

const statusTagClassMap = {
  accent: "ui-status-tag ui-status-tag--accent",
  positive: "ui-status-tag ui-status-tag--positive",
  warning: "ui-status-tag ui-status-tag--warning",
  negative: "ui-status-tag ui-status-tag--negative",
  neutral: "ui-status-tag ui-status-tag--neutral",
} as const;

const clampProgress = (value: number) => Math.max(0, Math.min(100, Math.round(value)));

const resolveRowKey = <T,>(record: T, rowKey: DataTableProps<T>["rowKey"]) =>
  typeof rowKey === "function" ? rowKey(record) : String(record[rowKey]);

const resolveCell = <T,>(record: T, column: ColumnDefinition<T>) => {
  if (column.render) {
    return column.render(record);
  }
  if (column.dataIndex) {
    return String(record[column.dataIndex] ?? "");
  }
  return "";
};

export const Button = ({ children, onClick, type = "button", variant = "primary", size = "default" }: ButtonProps) => (
  <button className={`${buttonClassMap[variant]}${buttonSizeClassMap[size]}`} onClick={onClick} type={type}>
    {children}
  </button>
);

export const StatusTag = ({ children, tone = "neutral" }: StatusTagProps) => (
  <span className={statusTagClassMap[tone]}>{children}</span>
);

export const ProgressBar = ({ value }: ProgressBarProps) => {
  const progress = clampProgress(value);

  return (
    <div aria-valuemax={100} aria-valuemin={0} aria-valuenow={progress} className="ui-progress" role="progressbar">
      <div className="ui-progress__fill" style={{ width: `${progress}%` }} />
    </div>
  );
};

export const DataTable = <T,>({ columns, data, rowKey }: DataTableProps<T>) => (
  <div className="ui-table-wrap">
    <table className="ui-table">
      <thead>
        <tr>
          {columns.map((column) => (
            <th key={column.key} scope="col">
              {column.title}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.map((record) => (
          <tr key={resolveRowKey(record, rowKey)}>
            {columns.map((column) => (
              <td key={column.key}>{resolveCell(record, column)}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

export const Tabs = ({ items, defaultActiveKey }: TabsProps) => {
  const generatedId = useId();
  const activeFallback = defaultActiveKey ?? items[0]?.key ?? "";
  const [activeKey, setActiveKey] = useState(activeFallback);
  const activeItem = items.find((item) => item.key === activeKey) ?? items[0];

  if (!activeItem) {
    return null;
  }

  return (
    <div className="ui-tabs">
      <div aria-label="section tabs" className="ui-tabs__list" role="tablist">
        {items.map((item) => {
          const tabId = `${generatedId}-${item.key}-tab`;
          const panelId = `${generatedId}-${item.key}-panel`;
          const isActive = item.key === activeItem.key;

          return (
            <button
              aria-controls={panelId}
              aria-selected={isActive}
              className={`ui-tabs__tab${isActive ? " ui-tabs__tab--active" : ""}`}
              id={tabId}
              key={item.key}
              onClick={() => setActiveKey(item.key)}
              role="tab"
              type="button"
            >
              {item.label}
            </button>
          );
        })}
      </div>
      <div
        aria-labelledby={`${generatedId}-${activeItem.key}-tab`}
        className="ui-tabs__panel"
        id={`${generatedId}-${activeItem.key}-panel`}
        role="tabpanel"
      >
        {activeItem.children}
      </div>
    </div>
  );
};
