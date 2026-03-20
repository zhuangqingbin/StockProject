import { Badge, Skeleton, Typography } from "antd";

import type { CategorySummary } from "../types";

type CategoryTreeProps = {
  categories: CategorySummary[];
  loading?: boolean;
  selectedCategory: string;
  onSelect: (categoryKey: string) => void;
};

const { Text } = Typography;

const CategoryTree = ({ categories, loading = false, selectedCategory, onSelect }: CategoryTreeProps) => {
  if (loading) {
    return <Skeleton active paragraph={{ rows: 8 }} title={false} />;
  }

  return (
    <div className="category-list">
      {categories.map((category) => (
        <button
          key={category.key}
          className={category.key === selectedCategory ? "category-item active" : "category-item"}
          onClick={() => onSelect(category.key)}
          type="button"
        >
          <span className="category-item-copy">
            <strong>{category.label}</strong>
            <Text className="category-item-key">{category.key}</Text>
          </span>
          <Badge count={category.table_count} color="#1053ff" />
        </button>
      ))}
    </div>
  );
};

export default CategoryTree;
