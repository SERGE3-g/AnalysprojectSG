from typing import Union, List, Dict, Optional, Tuple
import math
import logging
from decimal import Decimal, getcontext
import numpy as np
from scipy import integrate, optimize
import sympy as sp


class MathSolver:
    def __init__(self, precision: int = 10):
        """
        Inizializza il risolutore matematico

        Args:
            precision (int): Precisione decimale per i calcoli
        """
        self.power = None
        self.logarithm = None
        self.square_root = None
        self.logger = logging.getLogger(__name__)
        getcontext().prec = precision

        # Operazioni supportate e loro simboli
        self.operations = {
            '+': self.add,
            '-': self.subtract,
            '*': self.multiply,
            '/': self.divide,
            '^': self.power,
            'sqrt': self.square_root,
            'log': self.logarithm
        }

    # --- Operazioni Base ---

    def add(self, a: Union[int, float], b: Union[int, float]) -> float:
        """Addizione tra due numeri"""
        try:
            return float(Decimal(str(a)) + Decimal(str(b)))
        except Exception as e:
            self.logger.error(f"Errore nell'addizione: {str(e)}")
            raise ValueError("Errore nell'operazione di addizione")

    def subtract(self, a: Union[int, float], b: Union[int, float]) -> float:
        """Sottrazione tra due numeri"""
        try:
            return float(Decimal(str(a)) - Decimal(str(b)))
        except Exception as e:
            self.logger.error(f"Errore nella sottrazione: {str(e)}")
            raise ValueError("Errore nell'operazione di sottrazione")

    def multiply(self, a: Union[int, float], b: Union[int, float]) -> float:
        """Moltiplicazione tra due numeri"""
        try:
            return float(Decimal(str(a)) * Decimal(str(b)))
        except Exception as e:
            self.logger.error(f"Errore nella moltiplicazione: {str(e)}")
            raise ValueError("Errore nell'operazione di moltiplicazione")

    def divide(self, a: Union[int, float], b: Union[int, float]) -> float:
        """Divisione tra due numeri"""
        try:
            if b == 0:
                raise ValueError("Impossibile dividere per zero")
            return float(Decimal(str(a)) / Decimal(str(b)))
        except Exception as e:
            self.logger.error(f"Errore nella divisione: {str(e)}")
            raise ValueError("Errore nell'operazione di divisione")

    # --- Funzioni Avanzate ---

    def matrix_operations(self, matrix1: List[List[float]], matrix2: List[List[float]], operation: str) -> List[
        List[float]]:
        """
        Esegue operazioni matriciali

        Args:
            matrix1: Prima matrice
            matrix2: Seconda matrice
            operation: Tipo di operazione ('add', 'multiply', 'inverse', 'determinant')

        Returns:
            Risultato dell'operazione matriciale
        """
        try:
            m1 = np.array(matrix1)
            m2 = np.array(matrix2)

            if operation == 'add':
                return (m1 + m2).tolist()
            elif operation == 'multiply':
                return np.matmul(m1, m2).tolist()
            elif operation == 'inverse':
                return np.linalg.inv(m1).tolist()
            elif operation == 'determinant':
                return float(np.linalg.det(m1))
            else:
                raise ValueError("Operazione matriciale non supportata")
        except Exception as e:
            self.logger.error(f"Errore nell'operazione matriciale: {str(e)}")
            raise ValueError("Errore nell'operazione matriciale")

    def solve_polynomial(self, coefficients: List[float]) -> List[complex]:
        """
        Trova le radici di un polinomio

        Args:
            coefficients: Lista dei coefficienti [an, an-1, ..., a1, a0]

        Returns:
            Lista delle radici del polinomio
        """
        try:
            return np.roots(coefficients).tolist()
        except Exception as e:
            self.logger.error(f"Errore nel calcolo delle radici: {str(e)}")
            raise ValueError("Errore nel calcolo delle radici del polinomio")

    def integrate_function(self, func_str: str, lower: float, upper: float) -> float:
        """
        Calcola l'integrale definito di una funzione

        Args:
            func_str: Stringa rappresentante la funzione
            lower: Limite inferiore
            upper: Limite superiore

        Returns:
            Valore dell'integrale
        """
        try:
            x = sp.Symbol('x')
            func = sp.sympify(func_str)
            return float(sp.integrate(func, (x, lower, upper)))
        except Exception as e:
            self.logger.error(f"Errore nell'integrazione: {str(e)}")
            raise ValueError("Errore nel calcolo dell'integrale")

    def find_extrema(self, func_str: str, interval: Tuple[float, float]) -> Dict[str, float]:
        """
        Trova i punti di massimo e minimo di una funzione in un intervallo

        Args:
            func_str: Stringa rappresentante la funzione
            interval: Tupla (min, max) dell'intervallo

        Returns:
            Dizionario con i punti di massimo e minimo
        """
        try:
            x = sp.Symbol('x')
            func = sp.sympify(func_str)
            derivative = sp.diff(func, x)

            # Converti in funzione numerica per scipy
            f_lambda = sp.lambdify(x, func)

            # Trova i punti critici
            critical_points = []
            roots = sp.solve(derivative, x)
            for root in roots:
                root_float = float(root.evalf())
                if interval[0] <= root_float <= interval[1]:
                    critical_points.append(root_float)

            # Aggiungi gli estremi dell'intervallo
            critical_points.extend([interval[0], interval[1]])

            # Valuta la funzione nei punti critici
            values = [f_lambda(point) for point in critical_points]

            return {
                'maximum': {'x': critical_points[values.index(max(values))], 'y': max(values)},
                'minimum': {'x': critical_points[values.index(min(values))], 'y': min(values)}
            }
        except Exception as e:
            self.logger.error(f"Errore nella ricerca degli estremi: {str(e)}")
            raise ValueError("Errore nella ricerca degli estremi della funzione")

    def solve_system(self, coefficients: List[List[float]], constants: List[float]) -> List[float]:
        """
        Risolve un sistema di equazioni lineari

        Args:
            coefficients: Matrice dei coefficienti
            constants: Vettore dei termini noti

        Returns:
            Lista delle soluzioni
        """
        try:
            return np.linalg.solve(coefficients, constants).tolist()
        except Exception as e:
            self.logger.error(f"Errore nella risoluzione del sistema: {str(e)}")
            raise ValueError("Errore nella risoluzione del sistema di equazioni")

    def calculate_series(self, func_str: str, n: int) -> List[float]:
        """
        Calcola i primi n termini di una serie

        Args:
            func_str: Formula per l'n-esimo termine
            n: Numero di termini da calcolare

        Returns:
            Lista dei termini della serie
        """
        try:
            x = sp.Symbol('n')
            func = sp.sympify(func_str)
            f_lambda = sp.lambdify(x, func)

            series = [float(f_lambda(i)) for i in range(1, n + 1)]
            return series
        except Exception as e:
            self.logger.error(f"Errore nel calcolo della serie: {str(e)}")
            raise ValueError("Errore nel calcolo della serie")

    def geometric_calculations(self, shape: str, params: Dict[str, float]) -> Dict[str, float]:
        """
        Calcola area e perimetro di forme geometriche

        Args:
            shape: Tipo di forma ('circle', 'rectangle', 'triangle')
            params: Parametri della forma

        Returns:
            Dizionario con area e perimetro
        """
        try:
            if shape == 'circle':
                r = params['radius']
                return {
                    'area': math.pi * r * r,
                    'perimeter': 2 * math.pi * r
                }
            elif shape == 'rectangle':
                l = params['length']
                w = params['width']
                return {
                    'area': l * w,
                    'perimeter': 2 * (l + w)
                }
            elif shape == 'triangle':
                a = params['a']
                b = params['b']
                c = params['c']
                s = (a + b + c) / 2  # semi-perimetro
                area = math.sqrt(s * (s - a) * (s - b) * (s - c))  # formula di Erone
                return {
                    'area': area,
                    'perimeter': a + b + c
                }
            else:
                raise ValueError("Forma geometrica non supportata")
        except Exception as e:
            self.logger.error(f"Errore nei calcoli geometrici: {str(e)}")
            raise ValueError("Errore nei calcoli geometrici")

    def probability_calculations(self, event_type: str, params: Dict[str, Union[int, float, List[float]]]) -> float:
        """
        Calcola probabilità per vari tipi di distribuzioni

        Args:
            event_type: Tipo di evento/distribuzione
            params: Parametri per il calcolo

        Returns:
            Probabilità calcolata
        """
        try:
            if event_type == 'binomial':
                n = params['trials']
                p = params['probability']
                k = params['successes']
                return float(math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k)))
            elif event_type == 'normal':
                x = params['value']
                mu = params['mean']
                sigma = params['std_dev']
                return float(1 / (sigma * math.sqrt(2 * math.pi)) * math.exp(-((x - mu) ** 2) / (2 * sigma ** 2)))
            else:
                raise ValueError("Tipo di distribuzione non supportato")
        except Exception as e:
            self.logger.error(f"Errore nel calcolo della probabilità: {str(e)}")
            raise ValueError("Errore nel calcolo della probabilità")

    def optimize_function(self, func_str: str, bounds: Tuple[float, float], method: str = 'minimize') -> Dict[
        str, float]:
        """
        Ottimizza una funzione in un intervallo

        Args:
            func_str: Stringa rappresentante la funzione
            bounds: Intervallo di ricerca
            method: 'minimize' o 'maximize'

        Returns:
            Dizionario con il punto ottimale e il valore della funzione
        """
        try:
            x = sp.Symbol('x')
            func = sp.sympify(func_str)
            f_lambda = sp.lambdify(x, func)

            if method == 'minimize':
                result = optimize.minimize_scalar(f_lambda, bounds=bounds, method='bounded')
            else:  # maximize
                result = optimize.minimize_scalar(lambda x: -f_lambda(x), bounds=bounds, method='bounded')

            return {
                'x': float(result.x),
                'value': float(result.fun if method == 'minimize' else -result.fun)
            }
        except Exception as e:
            self.logger.error(f"Errore nell'ottimizzazione: {str(e)}")
            raise ValueError("Errore nell'ottimizzazione della funzione")


# Esempio di utilizzo
if __name__ == "__main__":
    solver = MathSolver(precision=10)

    try:
        # Test operazioni matriciali
        matrix1 = [[1, 2], [3, 4]]
        matrix2 = [[5, 6], [7, 8]]
        result = solver.matrix_operations(matrix1, matrix2, 'multiply')
        print("Prodotto matriciale:", result)

        # Test calcolo radici polinomio
        roots = solver.solve_polynomial([1, 0, -1])  # x² - 1 = 0
        print("Radici del polinomio:", roots)

        # Test integrazione
        integral = solver.integrate_function("x**2", 0, 1)
        print("Integrale di x² da 0 a 1:", integral)

        # Test calcoli geometrici
        circle_results = solver.geometric_calculations('circle', {'radius': 5})
        print("Area e perimetro del cerchio:", circle_results)

    except Exception as e:
        print(f"Si è verificato un errore: {str(e)}")