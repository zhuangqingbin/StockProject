import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Surface } from "../components/Surface";
import { Button } from "../components/ui";
import { stockBacktestClient } from "../services/client";
import { demoNotebookStatus, demoNotebookTemplates } from "../services/demoData";

export const NotebookPage = () => {
  const queryClient = useQueryClient();
  const { data: status } = useQuery({
    queryKey: ["notebook-status"],
    queryFn: stockBacktestClient.getNotebookStatus,
    initialData: demoNotebookStatus,
  });
  const { data: templates = [] } = useQuery({
    queryKey: ["notebook-templates"],
    queryFn: stockBacktestClient.getNotebookTemplates,
    initialData: demoNotebookTemplates,
  });
  const notebookMutation = useMutation({
    mutationFn: () => (status?.status === "running" ? stockBacktestClient.stopNotebook() : stockBacktestClient.startNotebook()),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["notebook-status"] });
    },
  });

  return (
    <div className="page-grid page-grid--two">
      <Surface eyebrow="Research Deck" title="研究入口">
        <div className="runtime-panel">
          <div>
            <span className="muted-copy">当前状态</span>
            <strong>{status?.status ?? "stopped"}</strong>
          </div>
          <Button onClick={() => void notebookMutation.mutateAsync()} size="large">
            {status?.status === "running" ? "停止 JupyterLab" : "启动 JupyterLab"}
          </Button>
        </div>
        {status?.url ? (
          <p className="muted-copy">
            当前地址{" "}
            <a className="inline-link" href={status.url} rel="noreferrer" target="_blank">
              {status.url}
            </a>
          </p>
        ) : null}
        <p className="muted-copy">
          前端只负责启动与跳转，深度实验仍然留在 Notebook 里，避免主工作台变成一块随意堆脚本的白板。
        </p>
      </Surface>

      <Surface eyebrow="Templates" title="分析模板">
        <div className="card-list">
          {templates.map((template) => (
            <div className="micro-card micro-card--wide" key={template.name}>
              <strong>{template.label}</strong>
              <p>{template.description}</p>
            </div>
          ))}
        </div>
      </Surface>
    </div>
  );
};
