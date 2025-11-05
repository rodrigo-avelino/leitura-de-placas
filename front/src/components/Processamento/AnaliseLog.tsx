import React, { useMemo } from "react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"; // Assumindo componente de Acordeão (Sanfona)
import { Card } from "@/components/ui/card";
import {
  CheckCircle2,
  Loader2,
  XCircle,
  Clock,
  Search,
  Image as ImageIcon,
} from "lucide-react"; // Ícones

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
  log: any[]; // Log completo do WebSocket (opcional, mas útil)
}

// --- Componente Auxiliar para o Ícone de Status (para manter o visual do mock) ---
const StatusIcon: React.FC<{ status: StepStatus }> = ({ status }) => {
  switch (status) {
    case "completed":
      return <CheckCircle2 className="h-5 w-5 text-green-500 mr-2 shrink-0" />;
    case "processing":
      return (
        <Loader2 className="h-5 w-5 text-blue-500 mr-2 animate-spin shrink-0" />
      );
    case "failed":
      return <XCircle className="h-5 w-5 text-red-500 mr-2 shrink-0" />;
    case "pending":
    default:
      return <Clock className="h-5 w-5 text-gray-400 mr-2 shrink-0" />;
  }
};

// --- Sub-componentes para Conteúdo Específico ---

// Componente simples para exibir imagens Base64
const ImageContainer: React.FC<{ title: string; src: string }> = ({
  title,
  src,
}) => (
  <div className="mt-4 border p-2 rounded-md bg-white">
    <p className="font-semibold mb-1 text-sm text-gray-700 flex items-center">
      <ImageIcon className="h-4 w-4 mr-1" /> {title}
    </p>
    <img
      src={src}
      alt={title}
      className="max-w-full h-auto rounded shadow-inner border"
      style={{ maxHeight: "250px", objectFit: "contain" }}
    />
  </div>
);

// Componente para exibir o Log de Tentativas (Step 3: Filtragem/Fallback)
const LogDisplay: React.FC<{ messages: string[] }> = ({ messages }) => (
  <div className="mt-4 p-3 bg-gray-50 border border-dashed rounded-md max-h-56 overflow-y-auto font-mono text-xs">
    <p className="font-bold text-gray-700 mb-1 flex items-center">
      <Search className="h-4 w-4 mr-1" /> Log de Tentativas (Fallback):
    </p>
    {messages.map((msg, index) => (
      <p
        key={index}
        className="text-gray-600 whitespace-pre-wrap leading-relaxed"
      >
        {msg}
      </p>
    ))}
    {messages.length === 0 && (
      <p className="text-gray-400 italic">
        Aguardando início do processo de filtragem...
      </p>
    )}
  </div>
);

// Componente para exibir o Resultado Final (Step 6)
const ResultadoFinalDisplay: React.FC<{
  result: Step["result"];
  status: StepStatus;
}> = ({ result, status }) => {
  if (!result) return null;
  const isSuccess = status === "completed";

  return (
    <div
      className="mt-4 p-4 border rounded-lg"
      style={{ borderColor: isSuccess ? "#10B981" : "#EF4444" }}
    >
      <p
        className="text-lg font-bold mb-2"
        style={{ color: isSuccess ? "#059669" : "#DC2626" }}
      >
        Status: {isSuccess ? "SUCESSO" : "FALHA"}
      </p>
      {result.placa && (
        <p className="text-2xl font-extrabold my-2 text-center">
          {result.placa}
        </p>
      )}

      <div className="space-y-1 text-sm text-gray-700">
        {result.padrao && (
          <p>
            Padrão Identificado:{" "}
            <span className="font-semibold">{result.padrao}</span>
          </p>
        )}
        {result.candidato && (
          <p>
            Candidato Vencedor:{" "}
            <span className="font-semibold">#{result.candidato}</span>
          </p>
        )}
        {!isSuccess && (
          <p className="text-red-600 font-medium">
            Motivo: Nenhuma placa válida foi encontrada ou erro no pipeline.
          </p>
        )}
      </div>
    </div>
  );
};

// --- Componente Principal AnaliseLog ---
const AnaliseLog = ({ steps }: AnaliseLogProps) => {
  // Identifica o item que deve estar aberto por padrão (o que está processando ou falhou)
  const defaultOpen = useMemo(() => {
    const activeStep = steps.find(
      (s) => s.status === "processing" || s.status === "failed"
    );
    return activeStep ? activeStep.id.toString() : steps.length.toString(); // Abre o último passo por padrão se estiver completo
  }, [steps]);

  // Função auxiliar para buscar imagens
  const getImages = (stepId: number) => {
    return steps.find((s) => s.id === stepId)?.images || {};
  };

  return (
    <Card className="p-6 h-full shadow-lg">
      <h2 className="text-xl font-bold mb-4 text-foreground">Log de Análise</h2>

      {/* O componente Acordeão é o que replica a "Sanfona" do seu design */}
      <Accordion type="single" defaultValue={defaultOpen} className="w-full">
        {steps.map((step) => (
          // O value do AccordionItem é usado para controle de estado aberto/fechado
          <AccordionItem key={step.id} value={step.id.toString()}>
            {/* HEADER da Sanfona: Mantém o visual com status e descrição */}
            <AccordionTrigger className="flex items-start justify-between py-3">
              <div className="flex items-start">
                <StatusIcon status={step.status} />
                <div className="text-left">
                  <p className="font-medium text-foreground">{step.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {step.description}
                  </p>
                </div>
              </div>
            </AccordionTrigger>

            {/* CONTEÚDO da Sanfona: Exibe as informações dinâmicas */}
            <AccordionContent className="pt-2 pb-4 text-sm text-muted-foreground ml-7 border-l-2 pl-4">
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
                  title="Contornos Detectados (Top 5 overlay)"
                  src={getImages(2).top_5_overlay!}
                />
              )}

              {/* Passo 3: Log de Fallback Dinâmico */}
              {step.id === 3 && <LogDisplay messages={step.logMessages} />}

              {/* Passo 4: Recorte da Placa (Vencedor) */}
              {step.id === 4 && getImages(4).candidate_crop_attempt && (
                <ImageContainer
                  title={`Recorte do Candidato Vencedor #${
                    step.result?.candidato || ""
                  }`}
                  src={getImages(4).candidate_crop_attempt!}
                />
              )}

              {/* Passo 5: Binarização e Segmentação (Lado a Lado) */}
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

              {/* Mensagens de Aguardando/Processando */}
              {step.status === "processing" && (
                <p className="italic text-blue-500">
                  Aguardando a próxima etapa de processamento...
                </p>
              )}
              {step.status === "pending" && (
                <p className="italic text-gray-400">
                  Esta etapa ainda não foi iniciada.
                </p>
              )}
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </Card>
  );
};

export default AnaliseLog;
