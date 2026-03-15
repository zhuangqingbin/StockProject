type DefaultWrappedExport<T> = T | { default: T };

export const resolveReactComponentExport = <T>(moduleExport: DefaultWrappedExport<T>): T => {
  if (typeof moduleExport === "object" && moduleExport !== null && "default" in moduleExport) {
    return moduleExport.default;
  }

  return moduleExport;
};
