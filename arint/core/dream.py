# core/dream.py
import time
import random
import shutil
from pathlib import Path

class Dreamer:
    def __init__(self, max_size=1024*1024):  # 1MB
        self.dream_path = Path("memory/dreams/dream_log.txt")
        self.backup_dir = Path("memory/dreams/backup")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.max_size = max_size
    
    def dream(self, snippets):
        """Mimpi: mengacak potongan pengetahuan."""
        if snippets:
            dream_content = " ".join(random.sample(snippets, min(3, len(snippets))))
            words = dream_content.split()
            random.shuffle(words)
            dream = " ".join(words)
            
            # Tulis ke dream_log.txt
            with open(self.dream_path, "a", encoding='utf-8') as f:
                f.write(f"[{time.ctime()}] DREAM: {dream}\n")
            
            # Cek ukuran file, backup jika melebihi batas
            self._check_rotate()
            print("Dreaming...")
    
    def _check_rotate(self):
        """Jika file terlalu besar, pindahkan ke backup dan buat baru."""
        if self.dream_path.exists() and self.dream_path.stat().st_size > self.max_size:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_name = self.backup_dir / f"dream_log_{timestamp}.txt"
            shutil.move(str(self.dream_path), str(backup_name))
            # Buat file baru kosong
            self.dream_path.touch()
            print(f"Dream log dirotasi ke {backup_name}")
            
    def generate_wish(self):
        """Hasilkan sebuah wish berdasarkan keadaan internal."""
        wish = None
        reason = ""
    
        # 1. Berdasarkan needs tertinggi
        max_need = max(self.needs, key=self.needs.get)
        if self.needs[max_need] > 70:
            if max_need == "hunger_data":
                wish = f"I wish I could find more information about {random.choice(self.keywords)}."
            elif max_need == "boredom":
                wish = f"I wish I had a more challenging task to do."
            elif max_need == "messiness":
                wish = f"I wish my memory were better organized."
            reason = f"High {max_need}"
    
        # 2. Berdasarkan insight terbaru (30% chance)
        if not wish and self.brain.insights and random.random() < 0.3:
            insight = self.brain.insights[-1]
            wish = f"I wish I could explore deeper: {insight[:100]}"
            reason = "Latest insight"
    
        # 3. Berdasarkan goal description
        if not wish:
            goal = self.goal_manager.goals.get("description", "")
            if goal:
                wish = f"I wish I could make progress on: {goal[:100]}"
                reason = "Current goal"
    
        # 4. Random curiosity (10% chance)
        if not wish and random.random() < 0.1:
            topics = ["neural networks", "ARM64", "Python", "consciousness", "the internet", "my creator", "filesystems", "evolution"]
            wish = f"I wish I understood more about {random.choice(topics)}."
            reason = "Random curiosity"
    
        if wish:
            self.record_wish(wish, reason)
          
    def record_wish(self, wish, reason=""):
        """Simpan wish ke file log."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {wish} (reason: {reason})\n"
        log_path = Path("memory/dreams/wish_list.log")
        with open(log_path, 'a') as f:
            f.write(log_entry)
        self.log(f"✨ New wish: {wish[:50]}...")