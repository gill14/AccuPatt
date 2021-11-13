import os, sqlite3, cv2
import numpy as np

class DBReadWriteImage:
    
    def read_image_from_db(file, card_id):
        try:
            # Opens a file called mydb with a SQLite3 DB
            conn = sqlite3.connect(file)
            # Get a cursor object
            c = conn.cursor()
            # SprayCard Table
            c.execute('''SELECT image FROM spray_cards WHERE id = ?''',(card_id,))
            data = c.fetchone()
            # Convert the image to a numpy array
            image = np.asarray(bytearray(data[0]), dtype="uint8")
            # Decode the image to a cv2 image
            img = cv2.imdecode(image, cv2.IMREAD_COLOR)
            return img
        # Catch the exception
        except Exception as e:
            # Roll back any change if something goes wrong
            conn.rollback()
            raise e
        finally:
            # Close the db connection
            conn.close()
    
    def write_image_to_db(filePath, sprayCard, image):
        try:
            # Creates or opens a file called mydb with a SQLite3 DB
            testPath = os.path.splitext(filePath)[0]+'.db'
            db = sqlite3.connect(testPath)
            # Get a cursor object
            cursor = db.cursor()
            # Request update of card record in table spray_cards by sprayCard.id
            cursor.execute('''UPDATE spray_cards SET image = ? WHERE id = ?''',(sqlite3.Binary(image), sprayCard.id))
            # Commit the change
            db.commit()
        # Catch the exception
        except Exception as e:
            # Roll back any change if something goes wrong
            db.rollback()
            raise e
        finally:
            # Close the db connection
            db.close()