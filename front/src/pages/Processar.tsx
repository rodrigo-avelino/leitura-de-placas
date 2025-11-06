// pages/Processar.tsx (Final e Completo)

import { useState, useCallback, useMemo } from "react";
import Navigation from "@/components/Layout/Navigation";
import UploadForm from "@/components/Processamento/UploadForm";
import ImageDisplay from "@/components/Processamento/ImageDisplay";
import DateTimeSelector from "@/components/Processamento/DateTimeSelector"; // <<< RE-IMPORTADO
import { usePlateWebSocket } from "@/hooks/usePlateWebSocket";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Upload, X, Loader2, CheckCircle2 } from "lucide-react";
import AnaliseLog from "@/components/Processamento/AnaliseLog";

// --- TIPAGENS (Inclusas para referência do TypeScript) ---
type FinalResult = {
  status: "ok" | "fail" | "error";
  texto_final: string | null;
  padrao_placa: string | null;
  id: number | null;
  data_registro: string | null;
};
// --- FIM das Tipagens ---

const Processar = () => {
  const [fileToProcess, setFileToProcess] = useState<File | null>(null);
  const [uploadedImageUrl, setUploadedImageUrl] = useState<string | null>(null);
  // 1. ESTADO REINTRODUZIDO PARA A DATA DE CAPTURA
  const [captureDateTime, setCaptureDateTime] = useState<Date>(new Date());

  const {
    isProcessing,
    steps,
    finalResult,
    processImage, // << O HOOK DEVE ACEITAR AGORA processImage(file, dateTime)
    resetState,
    log,
    candidateData,
    croppedPlateBase64,
    binarizedImageBase64,
    segmentedImageBase64,
  } = usePlateWebSocket();

  const handleFileSelect = useCallback(
    (file: File) => {
      resetState();
      const url = URL.createObjectURL(file);
      setUploadedImageUrl(url);
      setFileToProcess(file);
    },
    [resetState]
  );

  const handleSubmit = useCallback(() => {
    if (fileToProcess) {
      // 2. CHAMADA AJUSTADA PARA ENVIAR A DATA/HORA
      processImage(fileToProcess, captureDateTime);
    }
  }, [fileToProcess, processImage, captureDateTime]);

  const handleClear = useCallback(() => {
    if (uploadedImageUrl) {
      URL.revokeObjectURL(uploadedImageUrl);
    }
    setFileToProcess(null);
    setUploadedImageUrl(null);
    setCaptureDateTime(new Date()); // Reseta a data
    resetState();
  }, [resetState, uploadedImageUrl]);

  const isReadyToProcess = fileToProcess && !isProcessing;

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <main className="container mx-auto p-6 md:p-10">
        <h1 className="text-3xl font-bold mb-8">
          Análise de Placa em Tempo Real (ALPR)
        </h1>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Lado Esquerdo: Upload e Visualização */}
          <div className="space-y-6">
            {/* 3. COMPONENTE ADICIONADO AO LAYOUT */}
            <DateTimeSelector
              dateTime={captureDateTime}
              onDateTimeChange={setCaptureDateTime}
              disabled={isProcessing}
            />

            <Card>
              <CardHeader>
                <CardTitle>1. Enviar Imagem</CardTitle>
              </CardHeader>
              <CardContent>
                <UploadForm
                  onFileSelect={handleFileSelect}
                  disabled={isProcessing}
                />
              </CardContent>
            </Card>

            {/* ImageDisplay */}
            <ImageDisplay
              src={uploadedImageUrl}
              finalResult={finalResult}
              onProcess={handleSubmit}
              onClear={handleClear}
              isProcessing={isProcessing}
              // Miniaturas
              croppedPlate={croppedPlateBase64}
              binarizedImage={binarizedImageBase64}
              segmentedImage={segmentedImageBase64}
            />

            {/* Exibição do Resultado Final Simples */}
            {finalResult && (
              <Card
                className={`p-4 ${
                  finalResult.status === "ok"
                    ? "border-green-500"
                    : "border-red-500"
                } border-l-4`}
              >
                <p className="font-semibold text-lg flex items-center gap-2">
                  {finalResult.status === "ok" ? (
                    <CheckCircle2 className="w-5 h-5 text-green-500" />
                  ) : (
                    <X className="w-5 h-5 text-red-500" />
                  )}
                  {finalResult.status === "ok"
                    ? "Análise Concluída com Sucesso"
                    : "Análise Concluída com Falha"}
                </p>
                {finalResult.texto_final && (
                  <p className="text-3xl font-extrabold mt-2 text-center">
                    {finalResult.texto_final}
                  </p>
                )}
              </Card>
            )}
          </div>

          {/* Lado Direito: Log de Análise (Sanfona) */}
          <div>
            <AnaliseLog steps={steps} log={log} candidateData={candidateData} />
          </div>
        </div>
      </main>
    </div>
  );
};

export default Processar;
