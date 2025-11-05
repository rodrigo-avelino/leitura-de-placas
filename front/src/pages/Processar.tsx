import { useState, useEffect, useCallback } from "react";
import Navigation from "@/components/Layout/Navigation";
import UploadForm from "@/components/Processamento/UploadForm";
import ImageDisplay from "@/components/Processamento/ImageDisplay";
import AnaliseLog from "@/components/Processamento/AnaliseLog";
import DateTimeSelector from "@/components/Processamento/DateTimeSelector";
import { usePlateWebSocket } from "@/hooks/usePlateWebSocket"; // Importando o hook (essencial)
import { Card } from "@/components/ui/card";

// --- TIPAGENS (6 PASSOS DA DOCUMENTAÇÃO) ---
type StepStatus = "pending" | "processing" | "completed" | "failed";

interface Step {
  id: number;
  name: string;
  description: string;
  status: StepStatus;
  // Campos para guardar dados dinâmicos da API
  images: { [key: string]: string | null };
  logMessages: string[];
  result?: {
    placa: string | null;
    padrao: string | null;
    candidato: number | null;
  };
}

// NOVO Mapeamento dos passos baseado na Estrutura Visual da documentação (6 Sanfonas)
const initialSteps: Step[] = [
  {
    id: 1,
    name: "Pré-processamento",
    description: "Conversão para cinza e suavização.",
    status: "pending",
    images: {},
    logMessages: [],
  },
  {
    id: 2,
    name: "Bordas e Contorno",
    description: "Identificação de regiões candidatas.",
    status: "pending",
    images: {},
    logMessages: [],
  },
  {
    id: 3,
    name: "Filtragem de Contornos (Fallback)",
    description: "Tentativas de OCR e escolha do candidato.",
    status: "pending",
    images: {},
    logMessages: [],
  },
  {
    id: 4,
    name: "Recorte da Placa (Vencedor)",
    description: "Recorte da região que obteve sucesso.",
    status: "pending",
    images: {},
    logMessages: [],
  },
  {
    id: 5,
    name: "Binarização e Segmentação",
    description: "Imagens do processo final de OCR.",
    status: "pending",
    images: {},
    logMessages: [],
  },
  {
    id: 6,
    name: "Validação e Resultado Final",
    description: "Resumo do resultado da análise.",
    status: "pending",
    images: {},
    logMessages: [],
  },
];

// Mapeamento de Eventos da API para o ID das 6 Sanfonas da UI
const STEP_MAPPING: { [key: string]: number } = {
  // Passo 1
  start: 1,
  original: 1,
  preprocessing_done: 1,

  // Passo 2
  contours_done: 2,
  top_5_overlay: 2,

  // Passo 3 (Lógica de Fallback)
  candidates_data: 3,
  fallback_attempt: 3,
  ocr_attempt_result: 3,
  candidate_chosen: 3,
  fallback_failed_all: 3,

  // Passo 4
  candidate_crop_attempt: 4,

  // Passo 5
  final_binarization: 5,
  final_segmentation: 5,

  // Passo 6
  final_result: 6,
  error: 6,
};

const Processar = () => {
  // Estados do Processamento
  const [originalFile, setOriginalFile] = useState<File | null>(null);
  const [uploadedImage, setUploadedImage] = useState<string | null>(null); // URL do blob para preview
  const [steps, setSteps] = useState(initialSteps);
  const [captureDateTime, setCaptureDateTime] = useState<Date>(new Date());

  // Hook do WebSocket
  const {
    isProcessing,
    log, // Log de eventos brutos (usado para extrair informações)
    finalPlate, // Placa final (texto)
    status, // 'idle', 'processing', 'success', 'failed'
    processImage,
    closeConnection,
    croppedPlateBase64, // Imagem recortada do vencedor (opcional)
    // O hook deve retornar também o rank vencedor para o step 4
    candidateRankWinner,
    currentStepImages, // O hook deve retornar um objeto de imagens Base64
    currentLogMessages, // O hook deve retornar o log de tentativas
  } = usePlateWebSocket();

  // --- LÓGICA PRINCIPAL DE ATUALIZAÇÃO DOS STEPS (UI) ---
  useEffect(() => {
    if (log.length === 0) return;

    // O último log define a progressão
    const lastLog = log[log.length - 1];
    const currentStepId = STEP_MAPPING[lastLog.step] || 0;

    // Define o status de conclusão/falha
    const isFailure = status === "failed";
    const isSuccess = status === "success" && !isProcessing;

    setSteps((prevSteps) =>
      prevSteps.map((step) => {
        const newStep = { ...step };

        // 1. Marca passos anteriores como COMPLETED
        if (newStep.id < currentStepId) {
          newStep.status = "completed";
        }

        // 2. Marca o passo atual como PROCESSING
        if (newStep.id === currentStepId) {
          // Lógica de Falha
          if (
            lastLog.step === "fallback_failed_all" ||
            lastLog.step === "error"
          ) {
            newStep.status = "failed";
          }
          // Lógica de Sucesso (após o último passo)
          else if (isSuccess && newStep.id === 6) {
            newStep.status = "completed";
          }
          // Caso contrário, está em processamento
          else {
            newStep.status = "processing";
          }
        }

        // 3. Atualiza o conteúdo dinâmico do step (Imagens, Logs, Resultado)
        // Nota: Assumimos que o usePlateWebSocket compila estas informações
        if (newStep.id === 3 && currentLogMessages) {
          newStep.logMessages = currentLogMessages;
        }

        if (newStep.id === 6 && isSuccess) {
          newStep.result = {
            placa: finalPlate,
            padrao:
              log.find((l) => l.step === "final_result")?.padrao_placa || null,
            candidato: candidateRankWinner,
          };
          newStep.status = "completed";
        }

        // Sincroniza imagens globais (se o hook as fornecer)
        if (currentStepImages) {
          // Exemplo: Atualiza Step 1 com imagem de preprocessing_done
          if (newStep.id === 1 && currentStepImages.preprocessing_done) {
            newStep.images["main"] = currentStepImages.preprocessing_done;
          }
          // Exemplo: Atualiza Step 2 com imagem de top_5_overlay
          if (newStep.id === 2 && currentStepImages.top_5_overlay) {
            newStep.images["main"] = currentStepImages.top_5_overlay;
          }
          // Adicione lógica para Step 4 e 5 aqui, se as imagens vierem compiladas do hook
        }

        // Lógica de conclusão/falha final
        if (isSuccess && newStep.id === 6) {
          newStep.status = "completed";
        } else if (isFailure && newStep.id === 6) {
          newStep.status = "failed";
        }

        return newStep;
      })
    );
  }, [
    log,
    isProcessing,
    status,
    finalPlate,
    candidateRankWinner,
    currentLogMessages,
    currentStepImages,
  ]);

  // --- HANDLERS ---
  const handleFileSelect = (file: File) => {
    // 1. Limpa tudo
    handleClear();

    // 2. Prepara o File e URL para a UI
    setOriginalFile(file);
    const url = URL.createObjectURL(file);
    setUploadedImage(url);

    // 3. Reinicia os passos da UI
    setSteps(initialSteps);
  };

  const handleProcessClick = () => {
    if (originalFile) {
      processImage(originalFile); // Inicia a conexão e envia o File
    }
  };

  const handleClear = () => {
    if (uploadedImage) {
      URL.revokeObjectURL(uploadedImage);
    }
    setOriginalFile(null);
    setUploadedImage(null);
    setSteps(initialSteps); // Reset completo
    closeConnection();
  };

  // --- RENDERIZAÇÃO ---
  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <main className="container mx-auto px-6 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-foreground mb-2">
            Processamento de Imagem
          </h1>
          <p className="text-muted-foreground">
            Faça upload de uma imagem de veículo para análise da placa
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* COLUNA ESQUERDA: INPUTS E DISPLAY (DESIGN DO SEU MOCK) */}
          <div className="space-y-6">
            {/* 1. DateTimeSelector */}
            <DateTimeSelector
              dateTime={captureDateTime}
              onDateTimeChange={setCaptureDateTime}
              disabled={isProcessing || !!uploadedImage}
            />

            {/* 2. Upload/Display */}
            {!uploadedImage ? (
              <UploadForm
                onFileSelect={handleFileSelect}
                disabled={isProcessing}
              />
            ) : (
              <ImageDisplay
                imageUrl={uploadedImage}
                croppedPlate={croppedPlateBase64}
                onClear={handleClear}
                onProcess={handleProcessClick}
                isProcessing={isProcessing}
                status={status}
              />
            )}

            {/* 3. Card de Resultado Final */}
            {finalPlate && status === "success" && !isProcessing && (
              <Card className="p-6 border-2 border-green-500 bg-green-50">
                <h3 className="text-lg font-semibold text-green-700 mb-2">
                  Placa Identificada
                </h3>
                <p className="text-4xl font-bold text-green-900 text-center">
                  {finalPlate}
                </p>
              </Card>
            )}
            {status === "failed" && !isProcessing && (
              <Card className="p-6 border-2 border-red-500 bg-red-50">
                <h3 className="text-lg font-semibold text-red-700 mb-2">
                  Falha na Análise
                </h3>
                <p className="text-base text-red-900 text-center">
                  Não foi possível identificar uma placa válida.
                </p>
              </Card>
            )}
          </div>

          {/* COLUNA DIREITA: LOG DE ANÁLISE (DESIGN DO SEU MOCK) */}
          <div>
            {/* O componente AnaliseLog precisa usar o design de Acordeão com StatusIcons */}
            <AnaliseLog
              steps={steps}
              log={log} // Passa o log bruto para referência no AnaliseLog se necessário
            />
          </div>
        </div>
      </main>
    </div>
  );
};

export default Processar;
