#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Classes d'optimisation quantique pour différents cas d'usage cloud.
Ces classes utilisent Qiskit pour modéliser et résoudre des problèmes
d'optimisation liés aux ressources cloud, à l'équilibrage de charge et aux coûts.
"""

import logging
import numpy as np
from qiskit.quantum_info import Pauli
from qiskit.opflow import PauliSumOp, X, Z, I

# Configuration du logger
logger = logging.getLogger(__name__)

class BaseOptimizer:
    """Classe de base pour tous les optimiseurs quantiques."""
    
    def __init__(self):
        """Initialisation de la classe de base."""
        pass
    
    def build_qubit_operator(self):
        """Construit l'opérateur quantique à minimiser."""
        raise NotImplementedError("Cette méthode doit être implémentée dans les classes dérivées")
    
    def sample_most_likely(self, state_vector):
        """
        Échantillonne l'état le plus probable à partir du vecteur d'état.
        
        Args:
            state_vector: Vecteur d'état quantique
        
        Returns:
            Chaîne binaire représentant l'état le plus probable
        """
        n = int(np.log2(len(state_vector)))
        probabilities = np.abs(state_vector) ** 2
        most_likely_idx = np.argmax(probabilities)
        
        # Convertir l'index en une chaîne binaire
        binary = format(most_likely_idx, f'0{n}b')
        return binary
    
    def calculate_value(self, solution):
        """Calcule la valeur objectif pour une solution donnée."""
        raise NotImplementedError("Cette méthode doit être implémentée dans les classes dérivées")
    
    def decode_solution(self, solution):
        """Décode la solution binaire en une forme plus lisible."""
        raise NotImplementedError("Cette méthode doit être implémentée dans les classes dérivées")

class ResourceOptimizer(BaseOptimizer):
    """Optimiseur pour l'allocation des ressources cloud."""
    
    def __init__(self, nodes=5, cpus=8, memory=32):
        """
        Initialisation de l'optimiseur de ressources.
        
        Args:
            nodes: Nombre de noeuds à optimiser
            cpus: Nombre total de CPUs disponibles
            memory: Quantité totale de mémoire disponible en GB
        """
        super().__init__()
        self.nodes = nodes
        self.cpus = cpus
        self.memory = memory
        self.num_qubits = nodes * 3  # 3 qubits par noeud pour encoder différentes configurations
        
        # Générer des besoins en ressources simulés pour chaque noeud
        np.random.seed(42)  # Pour reproductibilité
        self.node_cpu_requirements = np.random.randint(1, 4, size=nodes)
        self.node_memory_requirements = np.random.randint(2, 8, size=nodes)
        
        logger.info(f"Optimisation des ressources initialisée avec {nodes} noeuds, {cpus} CPUs, {memory} GB RAM")
        logger.debug(f"Besoins CPU par noeud: {self.node_cpu_requirements}")
        logger.debug(f"Besoins mémoire par noeud: {self.node_memory_requirements}")
    
    def build_qubit_operator(self):
        """
        Construit un opérateur hamiltonien qui encode le problème d'optimisation des ressources.
        
        Returns:
            tuple: (opérateur quantique, constante de décalage)
        """
        # Initialiser un opérateur vide
        pauli_list = []
        offset = 0
        
        # Contrainte 1: Ne pas dépasser les CPU disponibles
        cpu_hamiltonian = 0
        for i in range(self.nodes):
            node_contribution = self.node_cpu_requirements[i]
            for j in range(3):  # 3 qubits par noeud
                qubit_idx = i * 3 + j
                weight = node_contribution * (2**j)
                
                # Créer un opérateur Z pour ce qubit avec le poids approprié
                pauli_str = ['I'] * self.num_qubits
                pauli_str[qubit_idx] = 'Z'
                
                pauli_op = PauliSumOp.from_list([("".join(pauli_str), weight/2)])
                cpu_hamiltonian += pauli_op
                
                # Ajuster la constante de décalage
                offset += weight/2
        
        # Contrainte 2: Ne pas dépasser la mémoire disponible
        memory_hamiltonian = 0
        for i in range(self.nodes):
            node_memory = self.node_memory_requirements[i]
            for j in range(3):  # 3 qubits par noeud
                qubit_idx = i * 3 + j
                weight = node_memory * (2**j)
                
                pauli_str = ['I'] * self.num_qubits
                pauli_str[qubit_idx] = 'Z'
                
                pauli_op = PauliSumOp.from_list([("".join(pauli_str), weight/2)])
                memory_hamiltonian += pauli_op
                
                # Ajuster la constante de décalage
                offset += weight/2
        
        # Combiner les hamiltoniens avec des pénalités pour les contraintes
        cpu_penalty = 10.0
        memory_penalty = 10.0
        
        # Pénaliser si on dépasse la capacité CPU
        cpu_excess = ((cpu_hamiltonian - offset) - self.cpus) ** 2
        
        # Pénaliser si on dépasse la capacité mémoire
        memory_excess = ((memory_hamiltonian - offset) - self.memory) ** 2
        
        # Objectif: Maximiser l'utilisation des ressources tout en respectant les contraintes
        hamiltonian = cpu_excess * cpu_penalty + memory_excess * memory_penalty
        
        # Ajouter un terme pour encourager l'utilisation des ressources
        utilization = 0
        for i in range(self.num_qubits):
            pauli_str = ['I'] * self.num_qubits
            pauli_str[i] = 'X'
            pauli_op = PauliSumOp.from_list([("".join(pauli_str), 0.1)])
            utilization += pauli_op
        
        hamiltonian = hamiltonian - utilization
        
        logger.info(f"Opérateur quantique construit avec {self.num_qubits} qubits")
        
        return hamiltonian, offset
    
    def calculate_value(self, solution):
        """
        Calcule la valeur d'optimisation pour une solution donnée.
        
        Args:
            solution: Chaîne binaire représentant l'état solution
        
        Returns:
            float: Score d'optimisation
        """
        total_cpu = 0
        total_memory = 0
        
        # Calculer les allocations totales de CPU et mémoire
        for i in range(self.nodes):
            node_config = int(solution[i*3:(i+1)*3], 2)
            cpu_allocated = self.node_cpu_requirements[i] * (node_config + 1) / 8
            memory_allocated = self.node_memory_requirements[i] * (node_config + 1) / 8
            
            total_cpu += cpu_allocated
            total_memory += memory_allocated
        
        # Pénaliser si on dépasse les limites
        if total_cpu > self.cpus:
            cpu_penalty = 100 * (total_cpu - self.cpus)
        else:
            cpu_penalty = 0
            
        if total_memory > self.memory:
            memory_penalty = 100 * (total_memory - self.memory)
        else:
            memory_penalty = 0
        
        # Score d'optimisation: maximiser l'utilisation tout en respectant les contraintes
        utilization_score = (total_cpu / self.cpus + total_memory / self.memory) / 2
        
        score = utilization_score - cpu_penalty - memory_penalty
        
        return score
    
    def decode_solution(self, solution):
        """
        Décode la solution binaire en allocation de ressources.
        
        Args:
            solution: Chaîne binaire représentant l'état solution
        
        Returns:
            dict: Allocation des ressources par noeud
        """
        allocation = {}
        
        for i in range(self.nodes):
            node_id = f"node-{i+1}"
            node_config = int(solution[i*3:(i+1)*3], 2)
            
            cpu_allocated = self.node_cpu_requirements[i] * (node_config + 1) / 8
            memory_allocated = self.node_memory_requirements[i] * (node_config + 1) / 8
            
            allocation[node_id] = {
                "cpu": round(cpu_allocated, 2),
                "memory": round(memory_allocated, 2),
                "config_value": node_config
            }
        
        return allocation
    
    def calculate_savings(self, solution):
        """
        Calcule les économies de ressources estimées.
        
        Args:
            solution: Chaîne binaire représentant l'état solution
        
        Returns:
            float: Pourcentage d'économies
        """
        # Calcul naïf sans optimisation (allocation maximale)
        naive_cpu = sum(self.node_cpu_requirements)
        naive_memory = sum(self.node_memory_requirements)
        
        # Allocation optimisée
        total_cpu = 0
        total_memory = 0
        
        for i in range(self.nodes):
            node_config = int(solution[i*3:(i+1)*3], 2)
            cpu_allocated = self.node_cpu_requirements[i] * (node_config + 1) / 8
            memory_allocated = self.node_memory_requirements[i] * (node_config + 1) / 8
            
            total_cpu += cpu_allocated
            total_memory += memory_allocated
        
        # Calculer les économies
        cpu_savings = (naive_cpu - total_cpu) / naive_cpu * 100
        memory_savings = (naive_memory - total_memory) / naive_memory * 100
        
        # Moyenne des économies
        avg_savings = (cpu_savings + memory_savings) / 2
        
        return avg_savings

class WorkloadBalancer(BaseOptimizer):
    """Optimiseur pour l'équilibrage de charge des workloads."""
    
    def __init__(self, num_services=10, num_nodes=3):
        """
        Initialisation de l'équilibreur de charge.
        
        Args:
            num_services: Nombre de services à équilibrer
            num_nodes: Nombre de noeuds disponibles
        """
        super().__init__()
        self.num_services = num_services
        self.num_nodes = num_nodes
        self.num_qubits = num_services * num_nodes  # 1 qubit pour chaque combinaison service-noeud
        
        # Générer des charges simulées pour chaque service
        np.random.seed(42)  # Pour reproductibilité
        self.service_loads = np.random.randint(1, 10, size=num_services)
        
        logger.info(f"Équilibreur de charge initialisé avec {num_services} services, {num_nodes} noeuds")
        logger.debug(f"Charges des services: {self.service_loads}")
    
    def build_qubit_operator(self):
        """
        Construit un opérateur hamiltonien qui encode le problème d'équilibrage de charge.
        
        Returns:
            tuple: (opérateur quantique, constante de décalage)
        """
        # Initialiser un opérateur vide
        hamiltonian = 0
        offset = 0
        
        # Contrainte 1: Chaque service doit être attribué à exactement un noeud
        for service in range(self.num_services):
            # Pour chaque service, somme de tous les qubits qui représentent son attribution à un noeud
            service_assignment = 0
            for node in range(self.num_nodes):
                qubit_idx = service * self.num_nodes + node
                pauli_str = ['I'] * self.num_qubits
                pauli_str[qubit_idx] = 'Z'
                
                pauli_op = PauliSumOp.from_list([("".join(pauli_str), 0.5)])
                service_assignment += pauli_op
                
                # Ajuster la constante de décalage
                offset += 0.5
            
            # Pénaliser si un service n'est pas exactement attribué à un noeud
            # (service_assignment - 1)^2 = service_assignment^2 - 2*service_assignment + 1
            hamiltonian += 10.0 * ((service_assignment)**2 - 2*service_assignment + 1)
        
        # Objectif: Équilibrer la charge entre les noeuds
        # Calculer la charge totale pour chaque noeud
        node_loads = []
        for node in range(self.num_nodes):
            node_load = 0
            for service in range(self.num_services):
                load = self.service_loads[service]
                qubit_idx = service * self.num_nodes + node
                
                pauli_str = ['I'] * self.num_qubits
                pauli_str[qubit_idx] = 'Z'
                
                pauli_op = PauliSumOp.from_list([("".join(pauli_str), load/2)])
                node_load += pauli_op
                
                # Ajuster la constante de décalage
                offset += load/2
            
            node_loads.append(node_load)
        
        # Pénaliser les différences de charge entre les noeuds
        for i in range(self.num_nodes):
            for j in range(i+1, self.num_nodes):
                # (node_loads[i] - node_loads[j])^2
                load_diff = (node_loads[i] - node_loads[j])**2
                hamiltonian += load_diff
        
        logger.info(f"Opérateur quantique construit avec {self.num_qubits} qubits")
        
        return hamiltonian, offset
    
    def decode_solution(self, solution):
        """
        Décode la solution binaire en attribution de services.
        
        Args:
            solution: Chaîne binaire représentant l'état solution
        
        Returns:
            dict: Attribution des services aux noeuds
        """
        attribution = {f"node-{i+1}": [] for i in range(self.num_nodes)}
        node_loads = [0] * self.num_nodes
        
        for service in range(self.num_services):
            service_id = f"service-{service+1}"
            service_load = self.service_loads[service]
            
            assigned_node = None
            for node in range(self.num_nodes):
                qubit_idx = service * self.num_nodes + node
                if solution[qubit_idx] == '1':
                    assigned_node = node
                    break
            
            if assigned_node is not None:
                node_id = f"node-{assigned_node+1}"
                attribution[node_id].append({
                    "service": service_id,
                    "load": int(service_load)
                })
                node_loads[assigned_node] += service_load
        
        # Ajouter les charges totales par noeud
        for node in range(self.num_nodes):
            node_id = f"node-{node+1}"
            attribution[node_id].append({
                "total_load": int(node_loads[node])
            })
        
        return attribution
    
    def calculate_balance_score(self, solution):
        """
        Calcule le score d'équilibrage pour une solution donnée.
        
        Args:
            solution: Chaîne binaire représentant l'état solution
        
        Returns:
            float: Score d'équilibrage (plus élevé = meilleur équilibrage)
        """
        node_loads = [0] * self.num_nodes
        
        # Calculer la charge de chaque noeud
        for service in range(self.num_services):
            service_load = self.service_loads[service]
            
            for node in range(self.num_nodes):
                qubit_idx = service * self.num_nodes + node
                if solution[qubit_idx] == '1':
                    node_loads[node] += service_load
        
        # Vérifier que chaque service est attribué exactement une fois
        assigned_services = 0
        for i in range(len(solution)):
            if solution[i] == '1':
                assigned_services += 1
        
        if assigned_services != self.num_services:
            return -1000  # Forte pénalité si la contrainte n'est pas respectée
        
        # Calculer la variance des charges comme mesure de déséquilibre
        mean_load = sum(node_loads) / self.num_nodes
        variance = sum((load - mean_load)**2 for load in node_loads) / self.num_nodes
        
        # Score d'équilibrage: inverse de la variance (plus la variance est faible, meilleur est l'équilibrage)
        if variance == 0:
            balance_score = 1000  # Équilibrage parfait
        else:
            balance_score = 100 / (1 + variance)
        
        return balance_score

class CostOptimizer(BaseOptimizer):
    """Optimiseur pour les coûts cloud multi-régions."""
    
    def __init__(self, num_regions=4, num_instance_types=5):
        """
        Initialisation de l'optimiseur de coûts.
        
        Args:
            num_regions: Nombre de régions cloud
            num_instance_types: Nombre de types d'instances disponibles
        """
        super().__init__()
        self.num_regions = num_regions
        self.num_instance_types = num_instance_types
        self.num_qubits = num_regions * num_instance_types
        
        # Générer des coûts simulés pour chaque combinaison région-instance
        np.random.seed(42)  # Pour reproductibilité
        self.instance_costs = np.random.uniform(0.1, 2.0, size=(num_regions, num_instance_types))
        self.instance_performance = np.random.uniform(0.5, 5.0, size=num_instance_types)
        
        # Besoins en performances
        self.performance_requirement = sum(self.instance_performance) * 0.6
        
        logger.info(f"Optimiseur de coûts initialisé avec {num_regions} régions, {num_instance_types} types d'instances")
        logger.info(f"Besoin en performance: {self.performance_requirement:.2f}")
    
    def build_qubit_operator(self):
        """
        Construit un opérateur hamiltonien qui encode le problème d'optimisation des coûts.
        
        Returns:
            tuple: (opérateur quantique, constante de décalage)
        """
        # Initialiser un opérateur vide
        hamiltonian = 0
        offset = 0
        
        # Objectif principal: Minimiser le coût total
        cost_hamiltonian = 0
        for region in range(self.num_regions):
            for instance in range(self.num_instance_types):
                cost = self.instance_costs[region, instance]
                qubit_idx = region * self.num_instance_types + instance
                
                pauli_str = ['I'] * self.num_qubits
                pauli_str[qubit_idx] = 'Z'
                
                pauli_op = PauliSumOp.from_list([("".join(pauli_str), cost/2)])
                cost_hamiltonian += pauli_op
                
                # Ajuster la constante de décalage
                offset += cost/2
        
        # Contrainte: Atteindre la performance requise
        performance_hamiltonian = 0
        for region in range(self.num_regions):
            for instance in range(self.num_instance_types):
                perf = self.instance_performance[instance]
                qubit_idx = region * self.num_instance_types + instance
                
                pauli_str = ['I'] * self.num_qubits
                pauli_str[qubit_idx] = 'Z'
                
                pauli_op = PauliSumOp.from_list([("".join(pauli_str), perf/2)])
                performance_hamiltonian += pauli_op
                
                # Ajuster la constante de décalage
                offset += perf/2
        
        # Pénaliser si la performance est insuffisante
        performance_penalty = 100.0 * ((performance_hamiltonian - offset) - self.performance_requirement)**2
        
        # Combinaison finale
        hamiltonian = cost_hamiltonian + performance_penalty
        
        logger.info(f"Opérateur quantique construit avec {self.num_qubits} qubits")
        
        return hamiltonian, offset
    
    def decode_solution(self, solution):
        """
        Décode la solution binaire en allocation d'instances.
        
        Args:
            solution: Chaîne binaire représentant l'état solution
        
        Returns:
            dict: Allocation des instances par région
        """
        allocation = {f"region-{i+1}": [] for i in range(self.num_regions)}
        total_cost = 0
        total_performance = 0
        
        for region in range(self.num_regions):
            region_id = f"region-{region+1}"
            region_cost = 0
            region_performance = 0
            
            for instance in range(self.num_instance_types):
                qubit_idx = region * self.num_instance_types + instance
                if solution[qubit_idx] == '1':
                    instance_id = f"instance-type-{instance+1}"
                    cost = self.instance_costs[region, instance]
                    perf = self.instance_performance[instance]
                    
                    allocation[region_id].append({
                        "instance": instance_id,
                        "cost": round(cost, 2),
                        "performance": round(perf, 2)
                    })
                    
                    region_cost += cost
                    region_performance += perf
                    total_cost += cost
                    total_performance += perf
            
            # Ajouter les totaux par région
            allocation[region_id].append({
                "region_cost": round(region_cost, 2),
                "region_performance": round(region_performance, 2)
            })
        
        # Ajouter les totaux globaux
        allocation["summary"] = {
            "total_cost": round(total_cost, 2),
            "total_performance": round(total_performance, 2),
            "performance_requirement": round(self.performance_requirement, 2),
            "performance_satisfied": total_performance >= self.performance_requirement
        }
        
        return allocation
    
    def calculate_savings(self, solution):
        """
        Calcule les économies de coûts estimées.
        
        Args:
            solution: Chaîne binaire représentant l'état solution
        
        Returns:
            float: Pourcentage d'économies
        """
        # Coût naïf: utiliser l'instance la plus performante dans chaque région
        naive_cost = 0
        for region in range(self.num_regions):
            best_perf_idx = np.argmax(self.instance_performance)
            naive_cost += self.instance_costs[region, best_perf_idx]
        
        # Coût optimisé
        optimized_cost = 0
        for region in range(self.num_regions):
            for instance in range(self.num_instance_types):
                qubit_idx = region * self.num_instance_types + instance
                if solution[qubit_idx] == '1':
                    optimized_cost += self.instance_costs[region, instance]
        
        # Calculer les économies
        if naive_cost > 0:
            cost_savings = (naive_cost - optimized_cost) / naive_cost * 100
        else:
            cost_savings = 0
        
        return cost_savings
