// pages/Processar.tsx (UI/UX Melhorado - Layout Otimizado + LocalStorage)

import { useState, useCallback, useEffect } from "react";
import Navigation from "@/components/Layout/Navigation";
import UploadForm from "@/components/Processamento/UploadForm";
import DateTimeSelector from "@/components/Processamento/DateTimeSelector";
import { usePlateWebSocket } from "@/hooks/usePlateWebSocket";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import AnaliseLog from "@/components/Processamento/AnaliseLog";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Activity, FileSearch, Settings, CheckCircle2 } from "lucide-react";

// --- TIPAGENS (Inclusas para referência do TypeScript) ---
type FinalResult = {
  status: "ok" | "fail" | "error";
  texto_final: string | null;
  padrao_placa: string | null;
  id: number | null;
  data_registro: string | null;
};

// Tipagem para o estado salvo no localStorage
interface ProcessarState {
  uploadedImageUrl: string | null;
  captureDateTime: string;
}
// --- FIM das Tipagens ---

const STORAGE_KEY = "processar-state";

const Processar = () => {
  const [fileToProcess, setFileToProcess] = useState<File | null>(null);
  const [uploadedImageUrl, setUploadedImageUrl] = useState<string | null>(null);
  const [captureDateTime, setCaptureDateTime] = useState<Date>(new Date());

  const {
    isProcessing,
    steps,
    finalResult,
    processImage,
    resetState,
    log,
    croppedPlateBase64,
    binarizedImageBase64,
    segmentedImageBase64,
  } = usePlateWebSocket();

  // Carrega o estado do localStorage ao montar o componente
  useEffect(() => {
    try {
      const savedState = localStorage.getItem(STORAGE_KEY);
      if (savedState) {
        const parsed: ProcessarState = JSON.parse(savedState);
        
        // Restaura a imagem se existir
        if (parsed.uploadedImageUrl) {
          setUploadedImageUrl(parsed.uploadedImageUrl);
        }
        
        // Restaura a data/hora
        if (parsed.captureDateTime) {
          setCaptureDateTime(new Date(parsed.captureDateTime));
        }
      }
    } catch (error) {
      console.error("Erro ao carregar estado do localStorage:", error);
    }
  }, []);

  // Salva o estado no localStorage sempre que mudar
  useEffect(() => {
    try {
      const stateToSave: ProcessarState = {
        uploadedImageUrl,
        captureDateTime: captureDateTime.toISOString(),
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(stateToSave));
    } catch (error) {
      console.error("Erro ao salvar estado no localStorage:", error);
    }
  }, [uploadedImageUrl, captureDateTime]);

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
      processImage(fileToProcess, captureDateTime);
    }
  }, [fileToProcess, processImage, captureDateTime]);

  const handleClear = useCallback(() => {
    if (uploadedImageUrl) {
      URL.revokeObjectURL(uploadedImageUrl);
    }
    setFileToProcess(null);
    setUploadedImageUrl(null);
    setCaptureDateTime(new Date());
    resetState();
    
    // Limpa o localStorage ao limpar o formulário
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (error) {
      console.error("Erro ao limpar localStorage:", error);
    }
  }, [resetState, uploadedImageUrl]);

  // Calcula progresso
  const completedSteps = steps.filter((s) => s.status === "completed").length;
  const totalSteps = steps.length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/30">
      <Navigation />

      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 lg:py-12 max-w-[1600px]">
        {/* Header Section com Status */}
        <div className="mb-10 space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <div className="flex items-center gap-3 mb-3">
                <h1 className="text-4xl lg:text-5xl font-bold text-foreground tracking-tight">
                  Análise de Placa Veicular
                </h1>
              </div>
              <p className="text-muted-foreground text-base sm:text-lg">
                Sistema de reconhecimento automático de placas (ALPR)
              </p>
            </div>

            {/* Status Badge - Só aparece quando está processando */}
            {isProcessing && (
              <div className="flex items-center gap-3 px-5 py-3 bg-blue-50 dark:bg-blue-950/30 border-2 border-blue-200 dark:border-blue-800 rounded-xl shadow-lg animate-pulse">
                <Activity className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                <div>
                  <p className="text-base font-bold text-blue-700 dark:text-blue-300">Processando</p>
                  <p className="text-sm text-blue-600 dark:text-blue-400">{completedSteps}/{totalSteps} etapas concluídas</p>
                </div>
              </div>
            )}

            {/* Badge de Sucesso */}
            {finalResult?.status === "ok" && (
              <Badge variant="default" className="h-12 px-6 text-base font-semibold bg-green-500 hover:bg-green-600 shadow-lg">
                <CheckCircle2 className="w-5 h-5 mr-2" />
                Análise Concluída
              </Badge>
            )}
          </div>

          <Separator className="bg-border/60" />
        </div>

        {/* Layout Responsivo Melhorado */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
          {/* Coluna Esquerda: Configuração e Upload */}
          <div className="xl:col-span-4 flex flex-col gap-6">
            {/* Card de Configurações */}
            <Card className="border-2 shadow-xl hover:shadow-2xl transition-all duration-300 shrink-0">
              <CardHeader className="pb-5 bg-gradient-to-br from-primary/5 to-transparent">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    <Settings className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <CardTitle className="text-xl font-bold">Configurações</CardTitle>
                    <CardDescription className="text-sm mt-1">
                      Defina a data e hora do registro
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-0 pb-6">
                <DateTimeSelector
                  dateTime={captureDateTime}
                  onDateTimeChange={setCaptureDateTime}
                  disabled={isProcessing}
                />
              </CardContent>
            </Card>

            {/* Card de Upload/Processamento */}
            <Card className="border-2 shadow-xl hover:shadow-2xl transition-all duration-300 flex-1 flex flex-col">
              <CardHeader className="pb-5 shrink-0 bg-gradient-to-br from-primary/5 to-transparent">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-xl font-bold">
                      {uploadedImageUrl ? "Imagem Carregada" : "Enviar Imagem"}
                    </CardTitle>
                    <CardDescription className="text-sm mt-1">
                      {uploadedImageUrl 
                        ? "Pronto para processar a análise" 
                        : "Faça upload de uma imagem de placa"}
                    </CardDescription>
                  </div>
                  {uploadedImageUrl && (
                    <div className="p-2 bg-green-100 dark:bg-green-950/30 rounded-lg">
                      <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400" />
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent className="pt-0 pb-6 flex-1 flex flex-col">
                <UploadForm
                  onFileSelect={handleFileSelect}
                  disabled={isProcessing}
                  uploadedImageUrl={uploadedImageUrl}
                  onProcess={handleSubmit}
                  onClear={handleClear}
                  isProcessing={isProcessing}
                  finalResult={finalResult}
                  croppedPlate={croppedPlateBase64}
                  binarizedImage={binarizedImageBase64}
                  segmentedImage={segmentedImageBase64}
                />
              </CardContent>
            </Card>
          </div>

          {/* Coluna Direita: Pipeline de Análise */}
          <div className="xl:col-span-8 flex">
            <AnaliseLog steps={steps} log={log} />
          </div>
        </div>
      </main>
    </div>
  );
};

export default Processar;
