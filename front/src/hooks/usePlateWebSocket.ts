import { useState, useRef, useCallback, useMemo } from "react";

// --- TIPAGENS ---
export interface LogEntry {
  step: string;
  message?: string;
  image?: string; // Imagens Base64
  candidate_rank?: number;
  ocr_text_raw?: string;
  valid_plates?: string[];
  placa?: string; // Placa do candidate_chosen
  padrao?: string; // Padrão do candidate_chosen

  // Propriedades do Resultado Final (final_result)
  status?: "ok" | "invalido";
  texto_final?: string;
  padrao_placa?: string; // Corrigido para final_result

  data?: any;
}

type ProcessingStatus = "idle" | "running" | "success" | "failed";

// Interface do Objeto de Retorno
interface WebSocketReturn {
  isProcessing: boolean;
  log: LogEntry[];
  finalPlate: string | null;
  status: ProcessingStatus;
  processImage: (file: File) => void;
  closeConnection: () => void;

  // Imagens Base64 individuais (para ImageDisplay e AnaliseLog)
  originalImageBase64: string | null;
  croppedPlateBase64: string | null;
  binarizedImageBase64: string | null;
  segmentedImageBase64: string | null;

  // Propriedades Adicionais (para facilitar o uso na UI)
  candidateRankWinner: number | null;
  currentLogMessages: string[];
  currentStepImages: { [key: string]: string | null }; // Objeto agrupador para AnaliseLog
}

export const usePlateWebSocket = (): WebSocketReturn => {
  // --- ESTADOS DE CONTROLE E RESULTADO ---
  const [isProcessing, setIsProcessing] = useState(false);
  const [log, setLog] = useState<LogEntry[]>([]);
  const [finalPlate, setFinalPlate] = useState<string | null>(null);
  const [status, setStatus] = useState<ProcessingStatus>("idle");
  const [candidateRankWinner, setCandidateRankWinner] = useState<number | null>(
    null
  );

  // --- ESTADOS DE IMAGEM INDIVIDUAL (Para Miniaturas e AnaliseLog) ---
  const [originalImageBase64, setOriginalImageBase64] = useState<string | null>(
    null
  );
  const [croppedPlateBase64, setCroppedPlateBase64] = useState<string | null>(
    null
  );
  const [binarizedImageBase64, setBinarizedImageBase64] = useState<
    string | null
  >(null);
  const [segmentedImageBase64, setSegmentedImageBase64] = useState<
    string | null
  >(null);

  // Novos estados para as imagens intermediárias (Passos 1 e 2 do AnaliseLog)
  const [preprocessedImageBase64, setPreprocessedImageBase64] = useState<
    string | null
  >(null);
  const [top5OverlayImageBase64, setTop5OverlayImageBase64] = useState<
    string | null
  >(null);

  const wsRef = useRef<WebSocket | null>(null);

  // --- Lógica de compilação de logs de fallback para o Step 3 ---
  const currentLogMessages = useMemo(() => {
    return log
      .filter(
        (entry) =>
          entry.step === "fallback_attempt" ||
          entry.step === "ocr_attempt_result" ||
          entry.step === "candidate_chosen" ||
          entry.step === "fallback_failed_all"
      )
      .map((entry) => {
        if (entry.step === "fallback_attempt") {
          return `Tentando Candidato #${entry.candidate_rank}...`;
        }
        if (entry.step === "ocr_attempt_result") {
          const isValid = entry.valid_plates && entry.valid_plates.length > 0;
          const statusText = isValid ? "Válido" : "Inválido";
          return ` -> Leitura: '${entry.ocr_text_raw}'. Resultado: ${statusText}.`;
        }
        if (entry.step === "candidate_chosen") {
          return ` -> Decisão: Candidato #${entry.candidate_rank} ('${entry.placa}', ${entry.padrao}) selecionado!`;
        }
        if (entry.step === "fallback_failed_all") {
          return entry.message || "Nenhum candidato produziu placa válida.";
        }
        return "";
      })
      .filter((msg) => msg.length > 0);
  }, [log]);

  // --- Objeto agrupador de imagens (currentStepImages) ---
  // Este objeto resolve o erro de tipagem e fornece todas as imagens para o AnaliseLog
  const currentStepImages = useMemo(() => {
    const imageMap: { [key: string]: string | null } = {};

    // Adiciona todas as imagens dos estados individuais (garante que nada é perdido)
    if (originalImageBase64) imageMap["original"] = originalImageBase64;
    if (preprocessedImageBase64)
      imageMap["preprocessing_done"] = preprocessedImageBase64;
    if (top5OverlayImageBase64)
      imageMap["top_5_overlay"] = top5OverlayImageBase64;
    if (croppedPlateBase64)
      imageMap["candidate_crop_attempt"] = croppedPlateBase64;
    if (binarizedImageBase64)
      imageMap["final_binarization"] = binarizedImageBase64;
    if (segmentedImageBase64)
      imageMap["final_segmentation"] = segmentedImageBase64;

    // Adiciona as imagens que estão apenas no log (se houver alguma)
    log.forEach((entry) => {
      if (entry.image && !imageMap[entry.step]) {
        imageMap[entry.step] = entry.image;
      }
    });

    return imageMap;
  }, [
    log,
    originalImageBase64,
    croppedPlateBase64,
    binarizedImageBase64,
    segmentedImageBase64,
    preprocessedImageBase64, // Dependência adicionada
    top5OverlayImageBase64, // Dependência adicionada
  ]);

  const processImage = useCallback(
    (file: File) => {
      // --- RESET DE ESTADOS ---
      setIsProcessing(true);
      setStatus("running");
      setLog([]);
      setFinalPlate(null);
      setCandidateRankWinner(null);
      setOriginalImageBase64(null);
      setCroppedPlateBase64(null);
      setBinarizedImageBase64(null);
      setSegmentedImageBase64(null);
      setPreprocessedImageBase64(null); // Reset
      setTop5OverlayImageBase64(null); // Reset

      const ws = new WebSocket("ws://127.0.0.1:8000/ws/processar-imagem");
      wsRef.current = ws;

      ws.onopen = () => {
        const reader = new FileReader();
        reader.onload = (e) => {
          if (e.target?.result instanceof ArrayBuffer) {
            // Envia ArrayBuffer (bytes brutos) para o FastAPI
            ws.send(e.target.result);
          } else {
            ws.close();
          }
        };
        reader.readAsArrayBuffer(file);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        setLog((prev) => [...prev, data]);

        // --- CAPTURA DE IMAGENS NOS ESTADOS INDIVIDUAIS ---
        if (data.image) {
          if (data.step === "original") {
            setOriginalImageBase64(data.image);
          }
          if (data.step === "preprocessing_done") {
            setPreprocessedImageBase64(data.image);
          } // Captura Passo 1
          if (data.step === "top_5_overlay") {
            setTop5OverlayImageBase64(data.image);
          } // Captura Passo 2

          // O backend pode enviar o crop final com 'candidate_crop_attempt'
          if (data.step === "candidate_crop_attempt") {
            setCroppedPlateBase64(data.image);
          }

          if (data.step === "final_binarization") {
            setBinarizedImageBase64(data.image);
          } // Captura Miniatura Binarização
          if (data.step === "final_segmentation") {
            setSegmentedImageBase64(data.image);
          } // Captura Miniatura Segmentação
        }

        // --- CAPTURA DE RESULTADOS ---
        if (data.step === "candidate_chosen") {
          setFinalPlate(data.placa);
          setCandidateRankWinner(data.candidate_rank);
        }

        // --- EVENTOS DE CONCLUSÃO / FALHA ---
        if (data.step === "final_result") {
          if (data.status === "ok") {
            setStatus("success");
          } else {
            setStatus("failed");
          }
          setIsProcessing(false);
          ws.close();
        }

        if (data.step === "fallback_failed_all" || data.step === "error") {
          setStatus("failed");
          setIsProcessing(false);
          ws.close();
        }
      };

      ws.onerror = (error) => {
        console.error("Erro no WebSocket:", error);
        setStatus("failed");
        setIsProcessing(false);
        setLog((prev) => [
          ...prev,
          { step: "error", message: "Erro na conexão ou no servidor" },
        ]);
      };

      ws.onclose = () => {
        if (status === "running") {
          setIsProcessing(false);
          setStatus("failed");
        }
      };
    },
    [status]
  );

  const closeConnection = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsProcessing(false);
    setStatus("idle");
    setLog([]);
    setFinalPlate(null);
    setCandidateRankWinner(null);
    setOriginalImageBase64(null);
    setCroppedPlateBase64(null);
    setBinarizedImageBase64(null);
    setSegmentedImageBase64(null);
    setPreprocessedImageBase64(null);
    setTop5OverlayImageBase64(null);
  }, []);

  // Objeto de retorno COMPLETO
  return {
    isProcessing,
    log,
    finalPlate,
    status,
    processImage,
    closeConnection,
    originalImageBase64,
    croppedPlateBase64,
    binarizedImageBase64,
    segmentedImageBase64,
    candidateRankWinner,
    currentLogMessages,
    currentStepImages,
  };
};
