import cv2
import numpy as np
import csv

class DoublePendulumTracker:
    def __init__(self, display_width=1200, frame_skip=3):  # Changé de 800 à 1200
        self.positions = []
        self.center = None
        self.current_frame = None
        self.display_frame = None
        self.points = {'center': None, 'm1': None, 'm2': None}
        self.point_order = ['center', 'm1', 'm2']
        self.current_point_index = 0
        self.display_width = display_width
        self.scale = 1.0
        self.frame_skip = frame_skip
        self.current_time = 0.0
        
    def calculate_angle(self, center, mass):
        """Calcule l'angle par rapport à la verticale (axe y négatif)"""
        dx = mass[0] - center[0]
        dy = mass[1] - center[1]
        angle = np.arctan2(dx, dy)
        return angle
    
    def scale_point(self, x, y):
        """Convertit les coordonnées de l'affichage vers l'image originale"""
        return (float(x / self.scale), float(y / self.scale))
        
    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            point_name = self.point_order[self.current_point_index]
            # Convertir les coordonnées d'affichage vers l'original
            self.points[point_name] = self.scale_point(x, y)
            
            # Dessiner sur la frame d'affichage
            cv2.circle(self.display_frame, (x, y), 5, (0, 255, 0), -1)
            cv2.putText(self.display_frame, point_name, (x+10, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.imshow('Frame', self.display_frame)
            
            self.current_point_index += 1
            
            if self.current_point_index >= len(self.point_order):
                # Calculer les angles
                t1 = self.calculate_angle(self.points['center'], self.points['m1'])
                t2 = self.calculate_angle(self.points['m1'], self.points['m2'])
                
                # Enregistrer: temps, center, t1, m1, t2, m2
                frame_data = [
                    self.current_time,
                    self.points['center'][0], self.points['center'][1],
                    t1,
                    self.points['m1'][0], self.points['m1'][1],
                    t2,
                    self.points['m2'][0], self.points['m2'][1]
                ]
                self.positions.append(frame_data)
                
                # Sauvegarder le centre pour les prochaines frames
                if self.center is None:
                    self.center = self.points['center']
                
                # Réinitialiser pour la prochaine frame
                self.points = {k: None for k in self.point_order}
                self.points['center'] = self.center
                self.current_point_index = 1
                
                print(f"Frame {len(self.positions)} | t={self.current_time:.3f}s | t1={t1:.3f} rad, t2={t2:.3f} rad")
    
    def track_video(self, video_path):
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print("Erreur: impossible d'ouvrir la vidéo")
            return None
        
        # Obtenir le FPS de la vidéo
        fps = cap.get(cv2.CAP_PROP_FPS)
        print(f"FPS de la vidéo: {fps}")
        
        cv2.namedWindow('Frame')
        cv2.setMouseCallback('Frame', self.mouse_callback)
        
        frame_count = 0
        processed_count = 0
        
        print("\nInstructions:")
        print("1. Cliquez sur: center -> m1 -> m2")
        print("   (t1 et t2 sont calculés automatiquement)")
        print(f"2. Traitement: 1 frame sur {self.frame_skip}")
        print("3. Appuyez sur ESPACE pour passer à la frame suivante")
        print("4. Appuyez sur 'q' pour quitter")
        print("5. Appuyez sur 's' pour sauvegarder et quitter\n")
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("Fin de la vidéo")
                # Sauvegarder automatiquement à la fin
                self.save_positions()
                break
            
            frame_count += 1
            
            # Traiter seulement toutes les N frames
            if frame_count % self.frame_skip != 0:
                continue
            
            processed_count += 1
            
            # Calculer le temps actuel
            self.current_time = frame_count / fps
            
            self.current_frame = frame.copy()
            
            # Calculer le facteur d'échelle
            height, width = self.current_frame.shape[:2]
            self.scale = self.display_width / width
            new_height = int(height * self.scale)
            
            # Redimensionner pour l'affichage
            self.display_frame = cv2.resize(self.current_frame, 
                                           (self.display_width, new_height))
            
            # Afficher les instructions sur la frame
            if self.current_point_index < len(self.point_order):
                next_point = self.point_order[self.current_point_index]
                cv2.putText(self.display_frame, f"Cliquez sur: {next_point}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Afficher le temps
            cv2.putText(self.display_frame, f"t = {self.current_time:.3f}s", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            
            cv2.imshow('Frame', self.display_frame)
            
            key = cv2.waitKeyEx(0)
            
            if key == ord('q'):
                self.save_positions()
                break
            elif key == ord('s'):
                self.save_positions()
                break
            elif key == 32:  # ESPACE
                if self.current_point_index == 0:
                    print("Marquez tous les points avant de passer à la frame suivante")
                else:
                    continue
        
        cap.release()
        cv2.destroyAllWindows()
        
        return np.array(self.positions) if len(self.positions) > 0 else None
    
    def save_positions(self, filename='positions.csv'):
        if len(self.positions) > 0:
            positions_array = np.array(self.positions)
            
            # Sauvegarder en CSV
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                # Écrire l'en-tête
                writer.writerow(['time', 'center_x', 'center_y', 't1', 'm1_x', 'm1_y', 't2', 'm2_x', 'm2_y'])
                # Écrire les données
                writer.writerows(positions_array)
            
            print(f"\nPositions sauvegardées dans {filename}")
            print(f"Shape: {positions_array.shape}")
            print(f"Format: [temps(s), center_x, center_y, t1(rad), m1_x, m1_y, t2(rad), m2_x, m2_y]")
            
            # Aussi sauvegarder en .npy pour numpy
            npy_filename = filename.replace('.csv', '.npy')
            np.save(npy_filename, positions_array)
            print(f"Aussi sauvegardé dans {npy_filename}")
            
            return positions_array
        else:
            print("Aucune position à sauvegarder")
            return None


# Utilisation
if __name__ == "__main__":
    # display_width=1200 pour une fenêtre plus grande
    tracker = DoublePendulumTracker(display_width=1200, frame_skip=3)
    
    video_path = "/home/karelsvbd/github/double-pendule/video/First_Video_2s.mp4"
    
    positions = tracker.track_video(video_path)
    
    if positions is not None:
        print(f"\nNombre total de frames traitées: {len(positions)}")
        print(f"Première frame: {positions[0]}")