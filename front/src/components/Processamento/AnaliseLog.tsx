import React, { useMemo } from "react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  CheckCircle2,
  Loader2,
  XCircle,
  Clock,
  Search,
  Image as ImageIcon,
  Sparkles,
  ZoomIn,
  AlertCircle,
  Activity,
} from "lucide-react";

// --- TIPAGENS (Mantidas idênticas ao Processar.tsx) ---
type StepStatus = "pending" | "processing" | "completed" | "failed";

interface Step {
  id: number;
  name: string;
  description: string;
  status: StepStatus;
  images: { [key: string]: string | null };
  logMessages: string[];
  result?: {
    placa: string | null;
    padrao: string | null;
    candidato: number | null;
  };
}

interface AnaliseLogProps {
  steps: Step[];
  log: Array<{ step?: string; [key: string]: unknown }>; // Log completo do WebSocket
}

// --- Componente Auxiliar para o Ícone de Status Melhorado ---
const StatusIcon: React.FC<{ status: StepStatus }> = ({ status }) => {
  switch (status) {
    case "completed":
      return (
        <div className="relative">
          <CheckCircle2 className="h-5 w-5 text-green-500 shrink-0" />
          <div className="absolute inset-0 bg-green-400 blur-sm opacity-30 rounded-full" />
        </div>
      );
    case "processing":
      return (
        <div className="relative">
          <Loader2 className="h-5 w-5 text-blue-500 animate-spin shrink-0" />
          <div className="absolute inset-0 bg-blue-400 blur-md opacity-40 rounded-full animate-pulse" />
        </div>
      );
    case "failed":
      return (
        <div className="relative">
          <XCircle className="h-5 w-5 text-red-500 shrink-0" />
          <div className="absolute inset-0 bg-red-400 blur-sm opacity-30 rounded-full" />
        </div>
      );
    case "pending":
    default:
      return <Clock className="h-5 w-5 text-gray-400 shrink-0" />;
  }
};

// Componente para Badge de Status
const StatusBadge: React.FC<{ status: StepStatus }> = ({ status }) => {
  const variants = {
    completed: { variant: "default" as const, label: "Concluído", className: "bg-green-500 hover:bg-green-600" },
    processing: { variant: "default" as const, label: "Processando", className: "bg-blue-500 hover:bg-blue-600 animate-pulse" },
    failed: { variant: "destructive" as const, label: "Falhou", className: "" },
    pending: { variant: "secondary" as const, label: "Pendente", className: "" },
  };

  const { variant, label, className } = variants[status];

  return (
    <Badge variant={variant} className={`ml-auto ${className}`}>
      {label}
    </Badge>
  );
};

// --- Sub-componentes para Conteúdo Específico ---

// Componente melhorado para exibir imagens Base64
const ImageContainer: React.FC<{ title: string; src: string; icon?: React.ReactNode }> = ({
  title,
  src,
  icon,
}) => {
  // Adiciona o prefixo data:image se não estiver presente
  const imageSrc = src.startsWith('data:image') 
    ? src 
    : `data:image/jpeg;base64,${src}`;

  return (
    <div className="mt-4 group relative overflow-hidden rounded-lg border-2 border-border bg-gradient-to-br from-background to-muted/20 p-3 shadow-md transition-all hover:shadow-lg hover:border-primary/50">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {icon || <ImageIcon className="h-4 w-4 text-primary" />}
          <p className="font-semibold text-sm text-foreground">{title}</p>
        </div>
        <ZoomIn className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
      </div>
      <div className="relative overflow-hidden rounded-md bg-muted/30 p-2">
        <img
          src={imageSrc}
          alt={title}
          className="max-w-full h-auto rounded border border-border/50 mx-auto transition-transform duration-300 group-hover:scale-105"
          style={{ maxHeight: "300px", objectFit: "contain" }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-background/5 to-transparent pointer-events-none" />
      </div>
    </div>
  );
};

// Componente melhorado para exibir o Log de Tentativas (Step 3: Filtragem/Fallback)
const LogDisplay: React.FC<{ messages: string[] }> = ({ messages }) => (
  <div className="mt-4 rounded-lg border-2 border-border bg-gradient-to-br from-muted/50 to-background overflow-hidden shadow-inner">
    <div className="bg-muted/80 px-4 py-2 border-b border-border flex items-center gap-2">
      <Search className="h-4 w-4 text-primary animate-pulse" />
      <p className="font-semibold text-sm text-foreground">
        Log de Tentativas (Fallback)
      </p>
      {messages.length > 0 && (
        <Badge variant="secondary" className="ml-auto">
          {messages.length} {messages.length === 1 ? "entrada" : "entradas"}
        </Badge>
      )}
    </div>
    <div className="p-4 max-h-64 overflow-y-auto font-mono text-xs custom-scrollbar">
      {messages.length > 0 ? (
        <div className="space-y-2">
          {messages.map((msg, index) => (
            <div
              key={index}
              className="flex items-start gap-2 p-2 rounded bg-background/50 border border-border/50 hover:border-primary/30 transition-colors"
            >
              <span className="text-muted-foreground font-bold min-w-[24px]">
                {index + 1}.
              </span>
              <p className="text-foreground whitespace-pre-wrap leading-relaxed flex-1">
                {msg}
              </p>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
          <Loader2 className="h-8 w-8 animate-spin mb-2 opacity-50" />
          <p className="italic text-sm">
            Aguardando início do processo de filtragem...
          </p>
        </div>
      )}
    </div>
  </div>
);

// Componente melhorado para exibir o Resultado Final (Step 6)
const ResultadoFinalDisplay: React.FC<{
  result: Step["result"];
  status: StepStatus;
}> = ({ result, status }) => {
  if (!result) return null;
  const isSuccess = status === "completed";

  return (
    <div
      className={`
        mt-4 p-6 rounded-xl border-2 shadow-lg overflow-hidden relative
        ${isSuccess 
          ? "bg-gradient-to-br from-green-50 to-emerald-50 border-green-400" 
          : "bg-gradient-to-br from-red-50 to-rose-50 border-red-400"
        }
      `}
    >
      {/* Efeito de fundo decorativo */}
      <div className={`absolute top-0 right-0 w-32 h-32 opacity-10 ${isSuccess ? "bg-green-400" : "bg-red-400"} rounded-full blur-3xl`} />
      
      {/* Header com ícone e status */}
      <div className="flex items-center justify-between mb-4 relative z-10">
        <div className="flex items-center gap-3">
          {isSuccess ? (
            <div className="p-2 bg-green-500 rounded-full">
              <CheckCircle2 className="h-6 w-6 text-white" />
            </div>
          ) : (
            <div className="p-2 bg-red-500 rounded-full">
              <AlertCircle className="h-6 w-6 text-white" />
            </div>
          )}
          <div>
            <p className={`text-lg font-bold ${isSuccess ? "text-green-700" : "text-red-700"}`}>
              {isSuccess ? "Análise Concluída com Sucesso!" : "Análise Falhou"}
            </p>
            <p className="text-xs text-muted-foreground">
              {isSuccess ? "Placa identificada com sucesso" : "Não foi possível identificar a placa"}
            </p>
          </div>
        </div>
        <Sparkles className={`h-6 w-6 ${isSuccess ? "text-green-500" : "text-red-500"} ${isSuccess && "animate-pulse"}`} />
      </div>

      {/* Placa identificada (destaque) */}
      {result.placa && (
        <div className="my-4 p-4 bg-white rounded-lg border-2 border-border shadow-sm relative z-10">
          <p className="text-xs text-muted-foreground text-center mb-1 uppercase tracking-wide">
            Placa Identificada
          </p>
          <p className="text-4xl font-extrabold text-center tracking-wider text-foreground font-mono">
            {result.placa}
          </p>
        </div>
      )}

      {/* Detalhes adicionais */}
      <div className="space-y-2 text-sm relative z-10">
        {result.padrao && (
          <div className="flex items-center justify-between p-3 bg-white/60 rounded-lg border border-border/50">
            <span className="text-muted-foreground font-medium">Padrão:</span>
            <Badge variant="outline" className="font-semibold">
              {result.padrao}
            </Badge>
          </div>
        )}
        {result.candidato !== null && result.candidato !== undefined && (
          <div className="flex items-center justify-between p-3 bg-white/60 rounded-lg border border-border/50">
            <span className="text-muted-foreground font-medium">Candidato Vencedor:</span>
            <Badge variant="outline" className="font-semibold">
              #{result.candidato}
            </Badge>
          </div>
        )}
        {!isSuccess && (
          <div className="flex items-start gap-2 p-3 bg-red-100/60 rounded-lg border border-red-300/50">
            <AlertCircle className="h-4 w-4 text-red-600 mt-0.5 shrink-0" />
            <p className="text-red-700 text-xs leading-relaxed">
              <span className="font-semibold">Motivo:</span> Nenhuma placa válida foi encontrada ou ocorreu um erro no pipeline de processamento.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

// --- Componente Principal AnaliseLog ---
const AnaliseLog = ({ steps }: AnaliseLogProps) => {
  // Identifica o item que deve estar aberto por padrão (somente o que está processando)
  const defaultOpen = useMemo(() => {
    const activeStep = steps.find(
      (s) => s.status === "processing"
    );
    return activeStep ? activeStep.id.toString() : undefined;
  }, [steps]);

  // Função auxiliar para buscar imagens
  const getImages = (stepId: number) => {
    return steps.find((s) => s.id === stepId)?.images || {};
  };

  // Calcula o progresso
  const completedSteps = steps.filter((s) => s.status === "completed").length;
  const progressPercentage = (completedSteps / steps.length) * 100;

  return (
    <Card className="overflow-hidden shadow-2xl border-2 hover:shadow-3xl transition-all duration-300 h-full flex flex-col w-full">
      {/* Header melhorado com progresso */}
      <div className="bg-gradient-to-r from-primary/15 via-primary/8 to-background p-7 border-b-2 border-border shrink-0">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/20 rounded-lg">
              <Activity className="w-6 h-6 text-primary" />
            </div>
            <h2 className="text-3xl font-bold text-foreground">
              Pipeline de Análise
            </h2>
          </div>
          <Badge variant="outline" className="text-base px-4 py-1.5 font-semibold border-2">
            {completedSteps} / {steps.length}
          </Badge>
        </div>
        
        {/* Barra de progresso */}
        <div className="relative w-full h-3 bg-muted rounded-full overflow-hidden shadow-inner">
          <div
            className="absolute top-0 left-0 h-full bg-gradient-to-r from-primary via-primary to-primary/80 transition-all duration-500 ease-out rounded-full shadow-lg"
            style={{ width: `${progressPercentage}%` }}
          />
          <div
            className="absolute top-0 left-0 h-full bg-primary/40 blur-md transition-all duration-500"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
        <div className="flex items-center justify-between mt-3">
          <p className="text-sm text-muted-foreground font-medium">
            Acompanhe cada etapa em tempo real
          </p>
          <p className="text-sm font-bold text-primary">
            {Math.round(progressPercentage)}%
          </p>
        </div>
      </div>

      {/* Accordion melhorado */}
      <div className="p-7 flex-1 overflow-y-auto custom-scrollbar">
        <Accordion type="single" collapsible defaultValue={defaultOpen} className="w-full space-y-5">
          {steps.map((step, index) => (
            <AccordionItem
              key={step.id}
              value={step.id.toString()}
              className={`
                border-2 rounded-xl overflow-hidden transition-all duration-300 shadow-md hover:shadow-xl
                ${step.status === "processing" ? "border-blue-500 shadow-lg shadow-blue-200 dark:shadow-blue-900 scale-[1.02]" : ""}
                ${step.status === "completed" ? "border-green-400/60" : ""}
                ${step.status === "failed" ? "border-red-400/60" : ""}
                ${step.status === "pending" ? "border-border" : ""}
              `}
            >
              {/* HEADER da Sanfona melhorado */}
              <AccordionTrigger className="hover:no-underline px-5 py-4 bg-gradient-to-r from-background to-muted/30 hover:to-muted/50 transition-colors">
                <div className="flex items-center gap-4 flex-1">
                  <div className="flex items-center justify-center w-10 h-10 rounded-full bg-gradient-to-br from-primary/20 to-primary/10 text-base font-bold text-primary border-2 border-primary/30 shadow-sm">
                    {index + 1}
                  </div>
                  <StatusIcon status={step.status} />
                  <div className="text-left flex-1">
                    <p className="font-bold text-base text-foreground">{step.name}</p>
                    <p className="text-sm text-muted-foreground mt-0.5">
                      {step.description}
                    </p>
                  </div>
                  <StatusBadge status={step.status} />
                </div>
              </AccordionTrigger>

            {/* CONTEÚDO da Sanfona melhorado */}
            <AccordionContent className="px-6 py-6 bg-muted/10">
              {/* Passo 1: Pré-processamento */}
              {step.id === 1 && getImages(1).preprocessing_done && (
                <ImageContainer
                  title="Imagem após Pré-processamento"
                  src={getImages(1).preprocessing_done!}
                />
              )}
              
              {/* Passo 2: Bordas e Contorno */}
              {step.id === 2 && getImages(2).top_5_overlay && (
                <ImageContainer
                  title="Contornos Detectados (Top 5)"
                  src={getImages(2).top_5_overlay!}
                  icon={<Search className="h-4 w-4 text-primary" />}
                />
              )}

              {/* Passo 3: Log de Fallback Dinâmico */}
              {step.id === 3 && <LogDisplay messages={step.logMessages} />}

              {/* Passo 4: Recorte da Placa (Vencedor) */}
              {step.id === 4 && getImages(4).candidate_crop_attempt && (
                <ImageContainer
                  title={`Recorte do Candidato Vencedor ${
                    step.result?.candidato ? `#${step.result.candidato}` : ""
                  }`}
                  src={getImages(4).candidate_crop_attempt!}
                  icon={<CheckCircle2 className="h-4 w-4 text-green-500" />}
                />
              )}

              {/* Passo 5: Binarização e Segmentação */}
              {step.id === 5 && (
                <div className="space-y-4">
                  {getImages(5).final_binarization && (
                    <ImageContainer
                      title="Resultado da Binarização"
                      src={getImages(5).final_binarization!}
                    />
                  )}
                  {getImages(5).final_segmentation && (
                    <ImageContainer
                      title="Caracteres Segmentados"
                      src={getImages(5).final_segmentation!}
                    />
                  )}
                </div>
              )}

              {/* Passo 6: Resultado Final */}
              {step.id === 6 &&
                (step.status === "completed" || step.status === "failed") && (
                  <ResultadoFinalDisplay
                    result={step.result}
                    status={step.status}
                  />
                )}

              {/* Mensagens de estado */}
              {step.status === "processing" && (
                <div className="flex items-center justify-center gap-2 py-6 text-blue-600">
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <p className="italic font-medium">
                    Processando esta etapa...
                  </p>
                </div>
              )}
              {step.status === "pending" && (
                <div className="flex items-center justify-center gap-2 py-6 text-muted-foreground">
                  <Clock className="h-5 w-5" />
                  <p className="italic">
                    Aguardando etapas anteriores...
                  </p>
                </div>
              )}
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
      </div>
    </Card>
  );
};

export default AnaliseLog;
