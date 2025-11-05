import { useState, useMemo } from "react";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Eye, Trash2, Calendar, Clock, Car, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";

// --- TIPAGENS CORRIGIDAS E COMPLETAS ---
type DeleteStatus = "idle" | "running" | "success" | "failed";

export interface Registro {
  // CORRIGIDO: Aceita string (WS) ou number (DB), como definido no hook
  id: number | string;
  placa: string;
  dataHora: string;
  imagemUrl: string;
  tipo_placa?: string; // Incluído
}

interface TabelaRegistrosProps {
  registros: Registro[];
  // Corrigido para aceitar id: number | string
  onDelete: (id: number | string) => void;
  // Adicionado o status de deleção do hook
  deleteStatus: DeleteStatus;
}

const TabelaRegistros = ({
  registros,
  onDelete,
  deleteStatus,
}: TabelaRegistrosProps) => {
  const [selectedRegistro, setSelectedRegistro] = useState<Registro | null>(
    null
  );

  // Lógica para mostrar feedback visual do status de deleção
  useMemo(() => {
    if (deleteStatus === "success") {
      toast.success("Registro removido com sucesso.");
      toast.dismiss(`delete-progress`);
    } else if (deleteStatus === "failed") {
      toast.error("Falha ao remover registro. Tente novamente.");
      toast.dismiss(`delete-progress`);
    }
  }, [deleteStatus]);

  const handleDelete = (id: number | string, placa: string) => {
    // Mostra o feedback de carregamento
    toast.loading(`Removendo registro da placa ${placa}...`, {
      id: `delete-progress`,
    });
    // Chama o handler do componente pai (que executa o deleteRegistro(id) do hook)
    onDelete(id);
  };

  // Helper para exibir o Badge de tipo de placa
  const renderTipoPlaca = (tipo?: string) => {
    if (!tipo) return null;
    const variant = tipo === "MERCOSUL" ? "default" : "secondary";
    return <Badge variant={variant}>{tipo}</Badge>;
  };

  // Verifica se a deleção está em andamento.
  const isDeleting = deleteStatus === "running";

  return (
    <>
      {registros.length === 0 ? (
        <Card className="p-12">
          <div className="flex flex-col items-center justify-center text-center space-y-4">
            <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
              <Car className="w-8 h-8 text-muted-foreground" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-foreground mb-1">
                Nenhum registro encontrado
              </h3>
              <p className="text-sm text-muted-foreground">
                Tente ajustar os filtros ou adicione novos registros
              </p>
            </div>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {registros.map((registro) => (
            <Card
              key={registro.id}
              className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-1 cursor-pointer"
              onClick={() => setSelectedRegistro(registro)}
            >
              <CardContent className="p-6 space-y-3">
                {/* Header com ID e Placa */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-accent/10">
                      <Car className="w-5 h-5 text-accent" />
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Placa</p>
                      <p className="font-mono font-bold text-xl text-foreground">
                        {registro.placa}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {renderTipoPlaca(registro.tipo_placa)}
                    <Badge className="font-mono">#{registro.id}</Badge>
                  </div>
                </div>

                <Separator />

                {/* Data e Hora */}
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-primary" />
                    <div>
                      <p className="text-xs text-muted-foreground">Data</p>
                      <p className="font-medium text-foreground">
                        {format(new Date(registro.dataHora), "dd/MM/yy", {
                          locale: ptBR,
                        })}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-success" />
                    <div>
                      <p className="text-xs text-muted-foreground">Horário</p>
                      <p className="font-medium text-foreground">
                        {format(new Date(registro.dataHora), "HH:mm", {
                          locale: ptBR,
                        })}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Ações */}
                <div className="flex gap-2 pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedRegistro(registro);
                    }}
                    disabled={isDeleting}
                  >
                    <Eye className="w-4 h-4 mr-1" />
                    Ver Detalhes
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    // Desabilita durante o processamento de deleção
                    disabled={isDeleting}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(registro.id, registro.placa);
                    }}
                  >
                    {isDeleting ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Trash2 className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Diálogo de Detalhes */}
      <Dialog
        open={!!selectedRegistro}
        onOpenChange={() => setSelectedRegistro(null)}
      >
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Detalhes do Registro</DialogTitle>
            <DialogDescription>
              Informações completas do veículo detectado
            </DialogDescription>
          </DialogHeader>

          {selectedRegistro && (
            <div className="space-y-6">
              {/* Informações do Registro */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Placa */}
                <Card className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-accent/10">
                      <Car className="w-5 h-5 text-accent" />
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Placa</p>
                      <p className="text-lg font-mono font-bold text-foreground">
                        {selectedRegistro.placa}
                      </p>
                    </div>
                  </div>
                </Card>
                {/* Data */}
                <Card className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <Calendar className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Data</p>
                      <p className="text-lg font-semibold text-foreground">
                        {format(
                          new Date(selectedRegistro.dataHora),
                          "dd/MM/yyyy",
                          { locale: ptBR }
                        )}
                      </p>
                    </div>
                  </div>
                </Card>
                {/* Horário */}
                <Card className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-success/10">
                      <Clock className="w-5 h-5 text-success" />
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Horário</p>
                      <p className="text-lg font-semibold text-foreground">
                        {format(
                          new Date(selectedRegistro.dataHora),
                          "HH:mm:ss",
                          { locale: ptBR }
                        )}
                      </p>
                    </div>
                  </div>
                </Card>
              </div>
              {/* FIM: grid grid-cols-1 md:grid-cols-3 gap-4 */}

              <Separator />

              {/* Imagem do Veículo */}
              <div>
                <h4 className="text-sm font-semibold text-foreground mb-3">
                  Imagem Capturada (Recorte)
                </h4>
                <div className="rounded-lg overflow-hidden border border-border bg-muted">
                  <img
                    src={selectedRegistro.imagemUrl}
                    alt={`Veículo placa ${selectedRegistro.placa}`}
                    className="w-full h-auto"
                  />
                </div>
              </div>

              {/* ID do Registro e Tipo de Placa */}
              <div className="flex items-center justify-between p-3 rounded-lg bg-muted">
                <span className="text-sm text-muted-foreground">
                  Tipo de Placa:
                  <Badge
                    className="ml-2"
                    variant={
                      selectedRegistro.tipo_placa === "MERCOSUL"
                        ? "default"
                        : "secondary"
                    }
                  >
                    {selectedRegistro.tipo_placa || "INDEFINIDO"}
                  </Badge>
                </span>
                <span className="font-mono font-semibold text-foreground">
                  #{selectedRegistro.id}
                </span>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
};

export default TabelaRegistros;
