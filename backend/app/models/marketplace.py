from app.extensions import db

class DispatchOffer(db.Model):
    __tablename__ = "dispatch_offers"
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer)
    driver_id = db.Column(db.Integer)
    price = db.Column(db.Float)
    status = db.Column(db.String(20))
