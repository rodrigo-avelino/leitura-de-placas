// hooks/usePlateWebSocket.ts

import { useState, useRef, useCallback, useMemo } from "react";
import { toast } from "sonner";
import { format } from "date-fns"; // IMPORTADO

// --- TIPAGENS ---
type StepStatus = "pending" | "processing" | "completed" | "failed";

interface WebSocketMessage {
  step: string;
  candidate_rank?: number;
  placa?: string;
  padrao?: string;
  image?: string;
  message?: string;
  log?: string;
  ocr_text_raw?: string;
  [key: string]: unknown;
}

export interface CandidateData {
  rank: number;
  score: number;
  seg_score: number;
  cores: { [key: string]: number };
}

export interface Step {
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

export interface FinalResult {
  status: "ok" | "fail" | "error";
  texto_final: string | null;
  padrao_placa: string | null;
  id: number | null;
  data_registro: string | null;
}

// Interface de Retorno COMPLETA
interface UsePlateWebSocketReturn {
  isProcessing: boolean;
  steps: Step[];
  log: WebSocketMessage[];
  finalResult: FinalResult | null;
  imageToProcessUrl: string | null;
  candidateData: CandidateData[];

  croppedPlateBase64: string | null;
  binarizedImageBase64: string | null;
  segmentedImageBase64: string | null;

  // MUDANÇA AQUI: Agora espera o File E a data
  processImage: (file: File, captureDateTime: Date) => void;
  resetState: () => void;
}

const INITIAL_STEPS: Step[] = [
  {
    id: 1,
    name: "Pré-processamento da Imagem",
    description: "Ajuste de cor, contraste e ruído.",
    status: "pending",
    images: {},
    logMessages: [],
  },
  {
    id: 2,
    name: "Detecção de Contornos (Candidatos)",
    description: "Identifica regiões da placa por morfologia.",
    status: "pending",
    images: {},
    logMessages: [],
  },
  {
    id: 3,
    name: "Filtragem e Validação Inicial (Fallback)",
    description: "Ranqueia candidatos e inicia testes de OCR e cor.",
    status: "pending",
    images: {},
    logMessages: [],
  },
  {
    id: 4,
    name: "Recorte da Placa (Vencedor)",
    description: "Isola e alinha o melhor candidato.",
    status: "pending",
    images: {},
    logMessages: [],
  },
  {
    id: 5,
    name: "Binarização e Segmentação",
    description: "Prepara os caracteres para leitura do OCR.",
    status: "pending",
    images: {},
    logMessages: [],
  },
  {
    id: 6,
    name: "Validação Final e Registro",
    description: "Verifica padrões, aplica OCR final e registra o resultado.",
    status: "pending",
    images: {},
    logMessages: [],
  },
];

const WEBSOCKET_URL = "ws://127.0.0.1:8000/ws/processar-imagem";

export const usePlateWebSocket = (): UsePlateWebSocketReturn => {
  // ... (Estados permanecem iguais) ...
  const [isProcessing, setIsProcessing] = useState(false);
  const [steps, setSteps] = useState<Step[]>(INITIAL_STEPS);
  const [log, setLog] = useState<WebSocketMessage[]>([]);
  const [finalResult, setFinalResult] = useState<FinalResult | null>(null);
  const [imageToProcessUrl, setImageToProcessUrl] = useState<string | null>(
    null
  );
  const [candidateData, setCandidateData] = useState<CandidateData[]>([]);

  const [croppedPlateBase64, setCroppedPlateBase64] = useState<string | null>(
    null
  );
  const [binarizedImageBase64, setBinarizedImageBase64] = useState<
    string | null
  >(null);
  const [segmentedImageBase64, setSegmentedImageBase64] = useState<
    string | null
  >(null);

  // Ref para acessar o log atual sem re-render
  const logRef = useRef<WebSocketMessage[]>([]);

  const resetState = useCallback(() => {
    setIsProcessing(false);
    setSteps(INITIAL_STEPS);
    setLog([]);
    setFinalResult(null);
    setImageToProcessUrl(null);
    setCandidateData([]);

    setCroppedPlateBase64(null);
    setBinarizedImageBase64(null);
    setSegmentedImageBase64(null);
  }, []);

  // Helper para atualizar um passo específico (inalterado)
  const updateStep = useCallback(
    (stepId: number, status?: StepStatus, updates?: Partial<Step>) => {
      setSteps((prevSteps) =>
        prevSteps.map((step) => {
          if (step.id === stepId) {
            return {
              ...step,
              ...updates,
              status: status !== undefined ? status : step.status,
              images: { ...step.images, ...(updates?.images || {}) },
              logMessages: [
                ...step.logMessages,
                ...(updates?.logMessages || []),
              ],
            };
          }
          if (status === "processing" && step.id < stepId) {
            return { ...step, status: "completed" };
          }
          return step;
        })
      );
    },
    []
  );

  // FUNÇÃO PRINCIPAL CORRIGIDA
  const processImage = useCallback(
    (file: File, captureDateTime: Date) => {
      resetState();
      setIsProcessing(true);
      const fileUrl = URL.createObjectURL(file);
      setImageToProcessUrl(fileUrl);
      let ws: WebSocket | null = null;
      let toastId: string | number = toast.loading("Conectando ao servidor...");

      // 1. Serializa a data para a Query String
      const isoDate = format(captureDateTime, "yyyy-MM-dd'T'HH:mm:ss.SSSxxx");
      const urlWithTime = `${WEBSOCKET_URL}?capture_time=${encodeURIComponent(
        isoDate
      )}`;

      try {
        ws = new WebSocket(urlWithTime); // Usa a URL com a data
      } catch (error) {
        toast.error(
          "Não foi possível conectar ao WebSocket. Verifique o servidor."
        );
        toast.dismiss(toastId);
        setIsProcessing(false);
        return;
      }

      ws.onopen = () => {
        toast.dismiss(toastId);
        toastId = toast.loading("Enviando imagem para análise...", {
          id: "processing-status",
        });

        const reader = new FileReader();
        reader.onload = (e) => {
          if (
            ws &&
            ws.readyState === 1 &&
            e.target?.result instanceof ArrayBuffer
          ) {
            ws.send(e.target.result); // Envia bytes
          }
        };
        reader.readAsArrayBuffer(file);
      };

      ws.onmessage = (event) => {
        if (typeof event.data !== "string") return;

        const data = JSON.parse(event.data);
        
        // Debug: Log de TODAS as mensagens recebidas
        console.log('[WebSocket] Mensagem recebida:', data.step, data.candidate_rank ? `(rank: ${data.candidate_rank})` : '');
        
        // Atualiza o log e o ref
        setLog((prevLog) => {
          const newLog = [...prevLog, data];
          logRef.current = newLog;
          return newLog;
        });

        // --- PROCESSAMENTO DE MENSAGENS DO WEBSOCKET ---
        switch (data.step) {
          case "start":
            toast.dismiss("processing-status");
            toast.loading("Processamento iniciado...", {
              id: "processing-status",
            });
            updateStep(1, "processing");
            break;

          case "preprocessing_done":
            updateStep(1, "completed", {
              images: { preprocessing_done: data.image },
            });
            updateStep(2, "processing");
            break;

          case "top_5_overlay":
            updateStep(2, "completed", {
              images: { top_5_overlay: data.image },
            });
            updateStep(3, "processing");
            break;

          case "candidates_data":
            setCandidateData(data.data);
            break;

          case "fallback_attempt":
          case "ocr_attempt_result":
          case "color_validation": {
            const logMessage =
              data.message ||
              `[Teste #${data.candidate_rank}] ${
                data.log || data.ocr_text_raw || ""
              }`;
            updateStep(3, "processing", { logMessages: [logMessage] });
            break;
          }

          case "candidate_crop_attempt":
            // Armazena temporariamente, mas não atualiza miniaturas ainda
            // Apenas quando soubermos qual é o vencedor
            console.log('[WebSocket] candidate_crop_attempt recebido - Rank:', data.candidate_rank);
            console.log('[WebSocket] Tem imagem?', !!data.image);
            if (data.image) {
              console.log('[WebSocket] Tamanho da imagem:', data.image.length, 'caracteres');
              console.log('[WebSocket] Primeiros 50 chars:', data.image.substring(0, 50));
            }
            break;

          case "candidate_chosen": {
            const winnerRank = data.candidate_rank;
            console.log('[WebSocket] ========================================');
            console.log('[WebSocket] Candidato escolhido:', winnerRank);
            console.log('[WebSocket] Log atual tem', logRef.current.length, 'mensagens');
            
            updateStep(3, "completed", {
              logMessages: [
                `-> Decisão: Candidato #${winnerRank} ('${data.placa}', ${data.padrao}) selecionado!`,
              ],
              result: {
                placa: data.placa,
                padrao: data.padrao,
                candidato: winnerRank,
              },
            });
            
            // Função para buscar e aplicar o crop
            const findAndApplyCrop = () => {
              const currentLog = logRef.current;
              
              // Debug: Mostra todos os crops disponíveis
              const allCrops = currentLog.filter((l: WebSocketMessage) => l.step === "candidate_crop_attempt");
              console.log('[WebSocket] Total de crops no log:', allCrops.length);
              allCrops.forEach((crop, idx) => {
                console.log(`[WebSocket] Crop ${idx + 1}: rank=${crop.candidate_rank}, temImagem=${!!crop.image}, tamanho=${crop.image?.length || 0}`);
              });
              
              const winnerCrop = currentLog.find(
                (l: WebSocketMessage) => 
                  l.step === "candidate_crop_attempt" && 
                  l.candidate_rank === winnerRank
              );
              
              if (winnerCrop && winnerCrop.image) {
                console.log('[WebSocket] ✅ Crop do vencedor ENCONTRADO!');
                console.log('[WebSocket] Rank:', winnerRank);
                console.log('[WebSocket] Tamanho da imagem:', winnerCrop.image.length, 'caracteres');
                console.log('[WebSocket] Primeiros 100 chars:', winnerCrop.image.substring(0, 100));
                
                setCroppedPlateBase64(winnerCrop.image);
                updateStep(4, "completed", {
                  images: { candidate_crop_attempt: winnerCrop.image },
                });
                return true;
              } else {
                console.warn('[WebSocket] ⚠️  Crop ainda não disponível, tentando novamente em 100ms...');
                return false;
              }
            };
            
            // Tenta buscar o crop imediatamente
            if (!findAndApplyCrop()) {
              // Se não encontrou, tenta novamente após um pequeno delay
              setTimeout(() => {
                if (!findAndApplyCrop()) {
                  console.error('[WebSocket] ❌ Crop do vencedor NÃO encontrado após retry!');
                  console.error('[WebSocket] Rank procurado:', winnerRank);
                  updateStep(4, "failed");
                }
              }, 100);
            }
            
            console.log('[WebSocket] ========================================');
            break;
          }

          case "final_binarization":
            // Atualiza o Step 5 e a miniatura da binarização
            console.log('[WebSocket] Binarização recebida');
            setBinarizedImageBase64(data.image);
            updateStep(5, "processing", {
              images: { final_binarization: data.image },
            });
            break;

          case "final_segmentation": {
            // Atualiza o Step 5 e a miniatura de segmentação
            console.log('[WebSocket] Segmentação recebida');
            setSegmentedImageBase64(data.image);
            updateStep(5, "completed", {
              images: { final_segmentation: data.image },
            });
            updateStep(6, "processing");
            break;
          }

          case "final_result": {
            const success = data.status === "ok";
            setFinalResult(data as FinalResult);
            toast.dismiss("processing-status");
            if (success) {
              toast.success(
                `Placa ${data.texto_final} registrada com sucesso!`
              );
              updateStep(6, "completed", {
                result: {
                  placa: data.texto_final,
                  padrao: data.padrao_placa,
                  candidato: null,
                },
              });
            } else {
              toast.error("Falha ao detectar uma placa válida.");
              updateStep(6, "failed", {
                result: {
                  placa: null,
                  padrao: null,
                  candidato: null,
                },
              });
            }
            setIsProcessing(false);
            ws?.close();
            break;
          }

          case "error":
            toast.dismiss("processing-status");
            toast.error(`Erro no servidor: ${data.message}`);
            setIsProcessing(false);
            updateStep(6, "failed", {
              logMessages: [`Erro: ${data.message}`],
            });
            ws?.close();
            break;

          default:
            break;
        }
      };

      ws.onclose = () => {
        setIsProcessing(false);
        toast.dismiss("processing-status");
      };

      ws.onerror = (e) => {
        console.error("WebSocket Error:", e);
        toast.dismiss("processing-status");
        toast.error("Erro inesperado na conexão WebSocket.");
        setIsProcessing(false);
        ws?.close();
      };

      // Cleanup function
      return () => {
        if (ws) ws.close();
        URL.revokeObjectURL(fileUrl);
      };
    },
    [resetState, updateStep]
  );

  return {
    isProcessing,
    steps,
    log,
    finalResult,
    imageToProcessUrl,
    candidateData,

    croppedPlateBase64,
    binarizedImageBase64,
    segmentedImageBase64,

    processImage,
    resetState,
  };
};
