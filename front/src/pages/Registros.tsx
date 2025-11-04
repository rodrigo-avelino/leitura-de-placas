import { useState, useMemo } from "react";
import Navigation from "@/components/Layout/Navigation";
import FiltrosRegistros from "@/components/Registros/FiltrosRegistros";
import TabelaRegistros, {
  Registro,
} from "@/components/Registros/TabelaRegistros";
import { Card, CardContent } from "@/components/ui/card";
import { BarChart3, FileText, TrendingUp, Clock } from "lucide-react";

const mockRegistros: Registro[] = [
  {
    id: 1,
    placa: "ABC-1234",
    dataHora: "2025-01-15T14:30:00",
    imagemUrl:
      "https://images.unsplash.com/photo-1485463611174-f302f6a5c1c9?w=800",
  },
  {
    id: 2,
    placa: "XYZ-5678",
    dataHora: "2025-01-15T15:45:00",
    imagemUrl:
      "https://images.unsplash.com/photo-1494976388531-d1058494cdd8?w=800",
  },
  {
    id: 3,
    placa: "DEF-9012",
    dataHora: "2025-01-15T16:20:00",
    imagemUrl:
      "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=800",
  },
  {
    id: 4,
    placa: "GHI-3456",
    dataHora: "2025-01-16T09:15:00",
    imagemUrl:
      "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=800",
  },
  {
    id: 5,
    placa: "JKL-7890",
    dataHora: "2025-01-16T11:30:00",
    imagemUrl:
      "https://images.unsplash.com/photo-1583121274602-3e2820c69888?w=800",
  },
];

const Registros = () => {
  const [registros, setRegistros] = useState<Registro[]>(mockRegistros);
  const [filteredRegistros, setFilteredRegistros] =
    useState<Registro[]>(mockRegistros);

  const handleFilter = (filters: {
    placa: string;
    dataInicio: string;
    dataFim: string;
  }) => {
    let filtered = [...registros];

    if (filters.placa) {
      filtered = filtered.filter((r) =>
        r.placa.toUpperCase().includes(filters.placa.toUpperCase())
      );
    }

    if (filters.dataInicio) {
      const dataInicio = new Date(filters.dataInicio);
      filtered = filtered.filter((r) => new Date(r.dataHora) >= dataInicio);
    }

    if (filters.dataFim) {
      const dataFim = new Date(filters.dataFim);
      dataFim.setHours(23, 59, 59, 999);
      filtered = filtered.filter((r) => new Date(r.dataHora) <= dataFim);
    }

    setFilteredRegistros(filtered);
  };

  const handleDelete = (id: number) => {
    setRegistros((prev) => prev.filter((r) => r.id !== id));
    setFilteredRegistros((prev) => prev.filter((r) => r.id !== id));
  };

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <main className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-foreground mb-2 bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            Consulta de Placas
          </h1>
        </div>

        {/* Filtros */}
        <div className="mb-6">
          <FiltrosRegistros onFilter={handleFilter} />
        </div>

        {/* Grid de Registros */}
        <TabelaRegistros
          registros={filteredRegistros}
          onDelete={handleDelete}
        />
      </main>
    </div>
  );
};

export default Registros;
