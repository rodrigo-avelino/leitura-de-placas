import React, { useMemo } from "react";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, Zap, RotateCcw, CheckCircle2, XCircle } from "lucide-react";

// --- TIPAGENS (Devem ser as mesmas do Processar.tsx e do Hook) ---
type ProcessingStatus = "idle" | "running" | "success" | "failed";

interface FinalResult {
  status: "ok" | "fail" | "error";
  texto_final: string | null;
  // Adicione outros campos necessários se forem usados aqui (ex: croppedPlate, binarizedImage)
}

// Interface principal do componente
export interface ImageDisplayProps {
  src: string | null; // URL Blob da imagem original para visualização
  finalResult: FinalResult | null;
  onProcess: () => void;
  onClear: () => void;
  isProcessing: boolean;

  // Imagens das miniaturas (Base64 passadas pelo hook)
  croppedPlate: string | null;
  binarizedImage: string | null;
  segmentedImage: string | null;
}
// --- FIM das TIPAGENS ---

// Sub-componente para Miniaturas de Etapas Finais
const ImageThumbnail: React.FC<{ title: string; image: string | null }> = ({
  title,
  image,
}) => (
  <div className="text-center">
    <p className="text-xs text-gray-500 mb-1 font-medium">{title}</p>
    <div className="w-full aspect-video border rounded-md overflow-hidden bg-gray-100 flex items-center justify-center">
      {image ? (
        // Exibe a imagem Base64
        <img src={image} alt={title} className="w-full h-full object-contain" />
      ) : (
        <span className="text-xs text-gray-400 p-1">Aguardando...</span>
      )}
    </div>
  </div>
);

const ImageDisplay: React.FC<ImageDisplayProps> = ({
  src,
  finalResult,
  onProcess,
  onClear,
  isProcessing,
  croppedPlate, // Miniaturas
  binarizedImage, // Miniaturas
  segmentedImage, // Miniaturas
}) => {
  // Determina o status geral da Card
  const statusText = useMemo(() => {
    if (isProcessing) return "PROCESSANDO...";
    if (finalResult?.status === "ok") return "ANÁLISE CONCLUÍDA";
    if (finalResult?.status === "fail" || finalResult?.status === "error")
      return "FALHA NA ANÁLISE";
    if (src) return "PRONTO PARA ANÁLISE";
    return "SELECIONE A IMAGEM";
  }, [isProcessing, finalResult, src]);

  const statusColor = useMemo(() => {
    if (isProcessing) return "border-blue-500 bg-blue-50 text-blue-800";
    if (finalResult?.status === "ok")
      return "border-green-500 bg-green-50 text-green-800";
    if (finalResult?.status === "fail" || finalResult?.status === "error")
      return "border-red-500 bg-red-50 text-red-800";
    return "border-gray-300 bg-white text-gray-700";
  }, [isProcessing, finalResult]);

  const canProcess = !isProcessing && src;

  return (
    <Card className={`shadow-xl transition-all ${statusColor}`}>
      <CardHeader className="p-4 border-b">
        <CardTitle className="flex items-center justify-between text-lg">
          Imagem Atual
          <span className="text-sm font-semibold uppercase">{statusText}</span>
        </CardTitle>
      </CardHeader>

      <CardContent className="p-4 space-y-4">
        {/* Imagem Principal */}
        <div className="relative w-full aspect-video rounded-lg overflow-hidden border">
          {src ? (
            <img
              src={src}
              alt="Imagem Original"
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-gray-200 text-gray-500">
              Nenhuma imagem selecionada.
            </div>
          )}

          {isProcessing && (
            <div className="absolute inset-0 bg-black bg-opacity-30 flex items-center justify-center">
              <Loader2 className="h-10 w-10 text-white animate-spin" />
            </div>
          )}
        </div>

        {/* Miniaturas de Processamento */}
        <div className="grid grid-cols-3 gap-2">
          <ImageThumbnail title="Recorte (Candidato)" image={croppedPlate} />
          <ImageThumbnail title="Binarização (Final)" image={binarizedImage} />
          <ImageThumbnail title="Segmentação (Final)" image={segmentedImage} />
        </div>
      </CardContent>

      <CardFooter className="flex justify-between p-4 border-t">
        {/* Botão Limpar */}
        <Button
          onClick={onClear}
          variant="outline"
          disabled={isProcessing}
          className="text-gray-600 hover:bg-gray-100"
        >
          <RotateCcw className="mr-2 h-4 w-4" /> Limpar
        </Button>

        {/* Botão Iniciar Análise */}
        <Button
          onClick={onProcess}
          disabled={!canProcess}
          className="bg-indigo-600 hover:bg-indigo-700 transition-colors"
        >
          {isProcessing ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processando...
            </>
          ) : (
            <>
              <Zap className="mr-2 h-4 w-4" />
              Iniciar Análise
            </>
          )}
        </Button>
      </CardFooter>
    </Card>
  );
};

export default ImageDisplay;
