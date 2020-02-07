#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import sys
import psycopg2
import csv
from datetime import date, datetime

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app,db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Show(db.Model):
    __tablename__='show'

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'))
    artist_id = db.Column(db.Integer,db.ForeignKey('artist.id'))
    artist = db.relationship("Artist", backref=db.backref('venue'))
    venue = db.relationship("Venue", backref=db.backref('artist'))


class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.String(200))
    image_link = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(200),default="Not looking for talent")
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    #artist_id = db.relationship('Show', backref=db.backref('venue'))

    def __repr__(self):
      return f'<Venue ID: {self.id}, name: {self.name}>'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    seeking_venue= db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(200),default="Not looking for a new venue")
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    #venue_id = db.relationship('Show', backref=db.backref('artist'))

    def __repr__(self):
      return f'<Artist ID: {self.id}, name: {self.name}>'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.




#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format = "EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  venue_data = Venue.query.order_by(Venue.city).order_by(Venue.state).all()
  current_time = datetime.now().strftime('%Y-%m-%d %H:%S:%M')
  new_data = []
  new_city_state = ''

  for venue in venue_data:
    if new_city_state == venue.city + venue.state:
      new_data[len(new_data)-1]["venues"].append({
        "id": venue.id,
        "name":venue.name,
        "num_upcoming_shows": 0
      })
    else:
      new_city_state = venue.city + venue.state
      new_data.append({
        "city":venue.city,
        "state":venue.state,
        "venues": [{
          "id": venue.id,
          "name":venue.name,
          "num_upcoming_shows": 0
        }]
      })
  return render_template('pages/venues.html', areas=new_data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term=request.form.get('search_term', '')
  new_term=str('%'+search_term+'%')
  response=db.session.query(Venue).filter(Venue.name.ilike(new_term)).order_by('name').all()
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue=Venue.query.get(venue_id)
  nr_upcoming_shows = db.session.query(Artist,Show).join(Show, Show.artist_id==Artist.id).filter(Show.venue_id==venue_id,Show.start_time >= datetime.now()).count()
  nr_completed_shows = db.session.query(Artist,Show).join(Show, Show.artist_id==Artist.id).filter(Show.venue_id==venue_id,Show.start_time < datetime.now()).count()
  upcoming_artists = db.session.query(Artist.id,Artist.name,Artist.image_link,Show.start_time,Show.venue_id).join(Show, Show.artist_id==Artist.id).filter(Show.venue_id==venue_id,Show.start_time >= datetime.now()).all()
  completed_artists = db.session.query(Artist.id,Artist.name,Artist.image_link,Show.start_time,Show.venue_id).join(Show, Show.artist_id==Artist.id).filter(Show.venue_id==venue_id,Show.start_time < datetime.now()).all()
  
  venue.upcoming_shows = []
  for u in upcoming_artists:
    artist_id=u[0]
    artist_name =u[1]
    artist_image_link=u[2]
    start_time = u[3].strftime("%Y%m%d %H:%M:%S")
    venue.upcoming_shows.append({'artist_id': artist_id, "artist_name": artist_name, "artist_image_link": artist_image_link, "start_time": start_time})
  
  venue.comp_art = []
  for c in completed_artists:
    artist_id=c[0]
    artist_name =c[1]
    artist_image_link=c[2]
    start_time = c[3].strftime("%Y%m%d %H:%M:%S")
    venue.comp_art.append({'artist_id': artist_id, "artist_name": artist_name, "artist_image_link": artist_image_link, "start_time": start_time})

  data={
    "id": venue.id,
    "name": venue.name,
    "genres": [venue.genres],
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": venue.comp_art,
    "upcoming_shows": venue.upcoming_shows,
    "past_shows_count": nr_completed_shows,
    "upcoming_shows_count": nr_upcoming_shows,
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  body = {}
  try:
    name = request.form.get('name', '')
    city = request.form.get('city', '')
    state = request.form.get('state', '')
    address = request.form.get('address', '')
    phone = request.form.get('phone', '')
    genres = request.form.get('genres', '')
    facebook_link = request.form.get('facebook_link', '')
    seeking_description = str("Not looking for talent")
    venue = Venue(
      name=name, 
      city=city, 
      state=state, 
      address=address,
      phone=phone,
      genres=genres,
      facebook_link=facebook_link, 
      seeking_talent=False, 
      seeking_description = seeking_description, 
      website = facebook_link)
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
    flash('Venue ' + request.form['name'] + ' experienced problems')
  finally:
    db.session.close()

  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data=Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term=request.form.get('search_term', '')
  new_term=str('%'+search_term+'%')
  response=db.session.query(Artist).filter(Artist.name.ilike(new_term)).order_by('name').all()
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  artist = Artist.query.get(artist_id)
  new_table = db.session.query(Venue,Show).join(Show, Show.venue_id==Venue.id).all()
  nr_upcoming_shows = db.session.query(Venue,Show).join(Show, Show.venue_id==Venue.id).filter(Show.artist_id==artist_id,Show.start_time >= datetime.now()).count()
  nr_completed_shows = db.session.query(Venue,Show).join(Show, Show.venue_id==Venue.id).filter(Show.artist_id==artist_id,Show.start_time < datetime.now()).count()
  upcoming_shows = db.session.query(Venue.id, Venue.name, Venue.image_link, Show.start_time, Show.artist_id).join(Show, Show.venue_id==Venue.id).filter(Show.artist_id==artist_id,Show.start_time >= datetime.now()).all()
  completed_shows = db.session.query(Venue.id, Venue.name, Venue.image_link, Show.start_time, Show.artist_id).join(Show, Show.venue_id==Venue.id).filter(Show.artist_id==artist_id,Show.start_time < datetime.now()).all()
  artist.up_shows = []
  for u in upcoming_shows:
    venue_id=u[0]
    venue_name =u[1]
    venue_image_link=u[2]
    start_time = u[3].strftime("%Y%m%d %H:%M:%S")
    artist.up_shows.append({'venue_id': venue_id, "venue_name": venue_name, "venue_image_link": venue_image_link, "start_time": start_time})
  
  artist.comp_shows = []
  for c in completed_shows:
    venue_id=u[0]
    venue_name =u[1]
    venue_image_link=u[2]
    start_time = u[3].strftime("%Y%m%d %H:%M:%S")
    artist.comp_shows.append({'venue_id': venue_id, "venue_name": venue_name, "venue_image_link": venue_image_link, "start_time": start_time})

  data1={
    "id": artist.id,
    "name": artist.name,
    "genres": [artist.genres],
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": artist.comp_shows,
    "upcoming_shows": artist.comp_shows,
    "past_shows_count": nr_upcoming_shows,
    "upcoming_shows_count": nr_completed_shows,
  }
  #data = list(filter(lambda d: d['id'] == artist_id, [data1, data2, data3]))[0]
  return render_template('pages/show_artist.html', artist=data1)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  body = {}
  try:
    name = request.form.get('name', '')
    city = request.form.get('city', '')
    state = request.form.get('state', '')
    phone = request.form.get('phone', '')
    genres = request.form.get('genres', '')
    facebook_link = request.form.get('facebook_link', '')
    artist = Artist(name=name, city=city, state=state, phone=phone,genres=genres,facebook_link=facebook_link)
    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  query_data=Show.query.all()
  new_data = []
  for d in  query_data:
    venue_name = str(db.session.query(Venue.name).filter(Venue.id==d.venue_id).all()[0][0])
    artist_name = str(db.session.query(Artist.name).filter(Artist.id==d.artist_id).all()[0][0])
    new_data.append({"start_time": str(d.start_time), "artist_image_link": "Empty", "venue_id":d.venue_id, "venue_name":venue_name, "artist_id": d.artist_id, "artist_name":artist_name}) 
  
  return render_template('pages/shows.html', shows=new_data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  error = False
  body = {}
  try:
    artist_id = int(request.form.get('artist_id', ''))
    venue_id = int(request.form.get('venue_id', ''))
    time = request.form.get('start_time', '')
    start_time = format_datetime(time)
    show = Show(start_time=start_time, venue_id = venue_id, artist_id = artist_id)
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
    flash('ERROR - Show was not listed!')
  finally:
    db.session.close()

  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
