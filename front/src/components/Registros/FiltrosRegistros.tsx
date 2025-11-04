import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Search, X, Calendar, Filter } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

interface FiltrosRegistrosProps {
  onFilter: (filters: { placa: string; dataInicio: string; dataFim: string }) => void;
}

const FiltrosRegistros = ({ onFilter }: FiltrosRegistrosProps) => {
  const [placa, setPlaca] = useState("");
  const [dataInicio, setDataInicio] = useState("");
  const [dataFim, setDataFim] = useState("");

  const handleSearch = () => {
    onFilter({ placa, dataInicio, dataFim });
  };

  const clearFilters = () => {
    setPlaca("");
    setDataInicio("");
    setDataFim("");
    onFilter({ placa: "", dataInicio: "", dataFim: "" });
  };

  const activeFiltersCount = [placa, dataInicio, dataFim].filter(Boolean).length;

  return (
    <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
      {/* Search Bar Principal */}
      <div className="relative flex-1 w-full">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
        <Input
          placeholder="Buscar por placa (ex: ABC-1234)..."
          value={placa}
          onChange={(e) => setPlaca(e.target.value.toUpperCase())}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          className="pl-10 h-12 text-base bg-card border-2 focus-visible:ring-2"
        />
      </div>

      {/* Filtro de Datas - Popover */}
      <Popover>
        <PopoverTrigger asChild>
          <Button variant="outline" className="h-12 gap-2 relative">
            <Calendar className="w-4 h-4" />
            <span className="hidden sm:inline">Período</span>
            {(dataInicio || dataFim) && (
              <Badge variant="secondary" className="ml-1 px-1.5 py-0 text-xs">
                {[dataInicio, dataFim].filter(Boolean).length}
              </Badge>
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-80" align="end">
          <div className="space-y-4">
            <h4 className="font-semibold text-sm flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              Filtrar por Período
            </h4>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">
                  Data Inicial
                </label>
                <Input
                  type="date"
                  value={dataInicio}
                  onChange={(e) => setDataInicio(e.target.value)}
                />
              </div>
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">
                  Data Final
                </label>
                <Input
                  type="date"
                  value={dataFim}
                  onChange={(e) => setDataFim(e.target.value)}
                />
              </div>
            </div>
          </div>
        </PopoverContent>
      </Popover>

      {/* Botão de Buscar */}
      <Button onClick={handleSearch} className="h-12 px-6">
        <Filter className="w-4 h-4 mr-2" />
        Filtrar
      </Button>

      {/* Limpar Filtros */}
      {activeFiltersCount > 0 && (
        <Button
          variant="ghost"
          onClick={clearFilters}
          className="h-12 text-muted-foreground hover:text-foreground"
        >
          <X className="w-4 h-4 mr-2" />
          Limpar
        </Button>
      )}
    </div>
  );
};

export default FiltrosRegistros;
