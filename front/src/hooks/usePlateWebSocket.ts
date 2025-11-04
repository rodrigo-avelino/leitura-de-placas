import { useState, useRef, useCallback } from "react";

export interface LogEntry {
  step: string;
  message?: string;
  image?: string;
  candidate_rank?: number;
  ocr_text_raw?: string;
  valid_plates?: string[];
  placa?: string;
  padrao?: string;
}

type ProcessingStatus = "idle" | "running" | "success" | "failed";

export const usePlateWebSocket = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [log, setLog] = useState<LogEntry[]>([]);
  const [finalPlate, setFinalPlate] = useState<string | null>(null);
  const [status, setStatus] = useState<ProcessingStatus>("idle");

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

  const wsRef = useRef<WebSocket | null>(null);

  const processImage = useCallback(
    (file: File) => {
      setIsProcessing(true);
      setStatus("running");
      setLog([]);
      setFinalPlate(null);
      setOriginalImageBase64(null);
      setCroppedPlateBase64(null);
      setBinarizedImageBase64(null);
      setSegmentedImageBase64(null);

      const ws = new WebSocket("ws://localhost:8001/ws/process");
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("WebSocket conectado");

        const reader = new FileReader();
        reader.onload = (e) => {
          if (e.target?.result) {
            const base64 = (e.target.result as string).split(",")[1];
            ws.send(
              JSON.stringify({
                type: "process",
                image: base64,
                filename: file.name,
              })
            );
          }
        };
        reader.readAsDataURL(file);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log("Mensagem recebida:", data);

        setLog((prev) => [...prev, data]);

        if (data.step === "original" && data.image) {
          setOriginalImageBase64(data.image);
        }

        if (data.step === "candidate_crop_attempt" && data.image) {
          setCroppedPlateBase64(data.image);
        }

        if (data.step === "final_binarization" && data.image) {
          setBinarizedImageBase64(data.image);
        }

        if (data.step === "final_segmentation" && data.image) {
          setSegmentedImageBase64(data.image);
        }

        if (data.step === "candidate_chosen") {
          setFinalPlate(data.placa);
          setStatus("success");
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
          { step: "error", message: "Erro na conexão" },
        ]);
      };

      ws.onclose = () => {
        console.log("WebSocket desconectado");
        if (isProcessing) {
          setIsProcessing(false);
        }
      };
    },
    [isProcessing]
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
    setOriginalImageBase64(null);
    setCroppedPlateBase64(null);
    setBinarizedImageBase64(null);
    setSegmentedImageBase64(null);
  }, []);

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
  };
};
