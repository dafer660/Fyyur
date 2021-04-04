# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel

from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import Form

import logging
from logging import Formatter, FileHandler

from datetime import datetime, timedelta

from sqlalchemy import distinct, func, between

from forms import *

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)

app.config.from_object('config')

db = SQLAlchemy(app)
migrate = Migrate(app=app, db=db)


# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(128), index=True)
    state = db.Column(db.String(128), index=True)
    address = db.Column(db.String(128))
    phone = db.Column(db.String(128))
    genres = db.Column(db.String())
    image_link = db.Column(db.String(512))
    facebook_link = db.Column(db.String(128))
    website_link = db.Column(db.String(128))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(255))
    listed_on = db.Column(db.Date, default=datetime.now())
    artists = db.relationship('Artist',
                              secondary='Shows',
                              backref=db.backref('artists', lazy=True))

    def __repr__(self):
        return '<Venue {}, {}>'.format(self.id, self.name)


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(128), index=True)
    state = db.Column(db.String(128), index=True)
    phone = db.Column(db.String(128))
    genres = db.Column(db.String())
    image_link = db.Column(db.String(512))
    facebook_link = db.Column(db.String(128))
    website_link = db.Column(db.String(128))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(255))
    listed_on = db.Column(db.Date, default=datetime.now())
    album = db.relationship('Album',
                            backref=db.backref('album', lazy=True))

    def __repr__(self):
        return '<Artist {}, {}>'.format(self.id, self.name)


class Shows(db.Model):
    __tablename__ = 'Shows'

    show_id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))
    start_time = db.Column(db.DateTime, default=datetime.now())

    def __repr__(self):
        return '<Show id: {}, Venue id: {}, Artist id: {}>'.format(self.show_id, self.venue_id, self.artist_id)


class Album(db.Model):
    __tablename__ = 'Album'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    launch_date = db.Column(db.Date, default=datetime.now())
    image_cover = db.Column(db.String())
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'),
                          nullable=False)
    songs = db.relationship('Songs', backref='songs', lazy=True)

    def __repr__(self):
        return '<Album: {}, {}>'.format(self.id, self.name)


class Songs(db.Model):
    __tablename__ = 'Songs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    duration = db.Column(db.Time)
    album_id = db.Column(db.Integer, db.ForeignKey('Album.id'),
                         nullable=False)

    def __repr__(self):
        return '<Song: {}, {}>'.format(self.id, self.name)


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    # added this because of data formatting:
    if isinstance(value, str):
        date = dateutil.parser.parse(value)
    else:
        date = value

    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    recent_venues = Venue.query.order_by('listed_on').limit(10).all()
    recent_artists = Artist.query.order_by('listed_on').limit(10).all()

    return render_template('pages/home.html', col_size=2,
                           recent_venues=recent_venues,
                           recent_artists=recent_artists)


# Albums
# ----------------------------------------------------------------------------#
@app.route('/albums')
def albums():
    artists = db.session.query(Artist.name, Artist.id).distinct(Artist.id, Artist.name).order_by('name').all()
    data = []

    for artist in artists:
        albums = Album.query \
            .filter_by(artist_id=artist.id) \
            .order_by('name').all()
        album_data = []

        data.append({
            'artist_id': artist.id,
            'artist_name': artist.name,
            'artist_albums': album_data
        })

        for album in albums:
            album_data.append({
                'album_id': album.id,
                'album_name': album.name,
                'num_songs': len(album.songs)
            })

    return render_template('pages/albums.html', albums=data)


@app.route('/album/<int:album_id>')
def show_album(album_id):
    album = Album.query.filter_by(id=album_id).first()
    return render_template('pages/show_album.html', album=album)


@app.route('/album/<int:album_id>/edit', methods=['GET'])
def edit_album(album_id):
    form = AlbumForm()
    album = Album.query.filter_by(id=album_id).first()
    artist = Artist.query.filter_by(id=album.artist_id).first()
    artists = Artist.query.all()

    form.album_name.data = album.name
    form.album_description.data = album.description
    form.album_launch_date.data = album.launch_date
    form.artist.choices = [(artist.id, artist.name) for artist in artists]
    form.artist.data = artist.id

    return render_template('forms/edit_album.html', form=form, album=album)


@app.route('/album/<int:album_id>/edit', methods=['POST'])
def edit_album_submission(album_id):
    album = Album.query.filter_by(id=album_id).first()

    if album:
        try:
            album.name = request.form.get('album_name', '')
            album.description = request.form.get('album_description', '')
            album.launch_date = request.form.get('album_launch_date', '')
            album.artist_id = request.form.get('artist', '')
            db.session.commit()
            flash('Album ' + request.form.get('album_name', '') + ' details were successfully updated!')
        except:
            db.session.rollback()
            flash('Album ' + request.form.get('album_name', '') + ' details could not be updated!')

    return redirect(url_for('show_album', album_id=album.id))


@app.route('/album/create', methods=['GET'])
def create_album_form():
    form = AlbumForm()
    artists = Artist.query.all()
    form.artist.choices = [(artist.id, artist.name) for artist in artists]

    return render_template('forms/new_album.html', form=form, artists=artists)


@app.route('/album/create', methods=['POST'])
def create_album_submission():
    form_data = request.form.to_dict()

    try:
        album = Album(name=form_data['album_name'],
                      description=form_data['album_description'],
                      launch_date=form_data['album_launch_date'],
                      artist_id=form_data['artist'])
        db.session.add(album)
        db.session.commit()
        flash('Album ' + request.form['album_name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        flash('An error occurred. Album ' + form_data['album_name'] + ' could not be listed.')
    finally:
        db.session.close()

    return redirect(url_for('index'))


@app.route('/song/create/<album_id>', methods=['GET'])
def create_song_form(album_id):
    form = SongForm()
    album = Album.query.filter_by(id=album_id).first()
    form.album.data = album

    return render_template('forms/new_song.html', form=form)


@app.route('/song/create/<int:album_id>', methods=['POST'])
def add_song(album_id):
    album = Album.query.filter_by(id=album_id).first()
    form_data = request.form.to_dict()
    song = Songs(
        name=form_data['song_name'],
        duration=form_data['song_duration'],
        album_id=album.id
    )
    try:
        if album:
            db.session.add(song)
            db.session.commit()
            flash('Song ' + song.name + ' was successfully added!')
    except:
        flash('Song ' + song.name + ' could not be added...!')
        db.session.rollback()

    # will not db.session.close() as I need album.id to redirect.
    return redirect(url_for('show_album', album_id=album.id))


@app.route('/song/remove/<int:song_id>', methods=['DELETE'])
def remove_song(song_id):
    song_id = request.get_json()['song']
    song = Songs.query.filter_by(id=song_id).first()
    try:
        if song:
            db.session.delete(song)
            db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()

    # return jsonify and handle the redirect with javascript
    # as the DELETE method has issues.
    return jsonify("success", 200)


# Venues
#  ----------------------------------------------------------------
@app.route('/venues')
def venues():
    areas = db.session.query(Venue.city, Venue.state).distinct(Venue.city, Venue.state).order_by('state').all()
    data = []
    for area in areas:
        venues = Venue.query \
            .filter_by(state=area.state) \
            .filter_by(city=area.city) \
            .order_by('name').all()
        venue_data = []

        data.append({
            'city': area.city,
            'state': area.state,
            'venues': venue_data
        })

        for venue in venues:
            shows = Shows.query \
                .filter_by(venue_id=venue.id) \
                .order_by('show_id').all()

            venue_data.append({
                'id': venue.id,
                'name': venue.name,
                'num_upcoming_shows': len(shows)
            })

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '')

    results = Venue.query.filter(
        Venue.name.ilike('%' + search_term + '%'),
    ).all()

    return render_template('pages/search_venues.html', results=results,
                           search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.filter_by(id=venue_id).first()
    shows = Shows.query.filter_by(venue_id=venue.id).all()

    queries = db.session.query(
        Artist, Shows, Venue
    ).filter(
        Venue.id == venue_id,
        Shows.venue_id == venue_id
    ).all()

    u_shows = []
    p_shows = []

    for show in shows:
        current_artist = Artist.query.filter_by(id=show.artist_id).first()
        if show.start_time <= datetime.now():
            p_shows.append({
                "artist_id": current_artist.id,
                "artist_name": current_artist.name,
                "artist_image_link": current_artist.image_link,
                "start_time": show.start_time
            })
        if show.start_time > datetime.now():
            u_shows.append({
                "artist_id": current_artist.id,
                "artist_name": current_artist.name,
                "artist_image_link": current_artist.image_link,
                "start_time": show.start_time
            })

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website_link,
        "facebook_link": venue.facebook_link,
        "listed_on": venue.listed_on,
        "seeking_talent": True if venue.seeking_talent == 'y' else False,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": p_shows,
        "upcoming_shows": u_shows,
        "past_shows_count": len(p_shows),
        "upcoming_shows_count": len(u_shows),
    }

    return render_template('pages/show_venue.html', venue=data)


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form_data = request.form.to_dict()

    genres = ','.join(request.form.getlist('genres'))
    seeking_talent = True if request.form.get('seeking_talent') == 'y' else False

    try:
        venue = Venue(name=form_data['name'], city=form_data['city'], state=form_data['state'],
                      address=form_data['address'],
                      phone=form_data['phone'], genres=genres, facebook_link=form_data['facebook_link'],
                      image_link=form_data['image_link'], website_link=form_data['website_link'],
                      seeking_talent=seeking_talent, seeking_description=form_data['seeking_description'])
        db.session.add(venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        flash('An error occurred. Venue ' + form_data['name'] + ' could not be listed.')
    finally:
        db.session.close()

    return redirect(url_for('index'))


@app.route('/venues/<int:venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    venue_id = request.get_json()['venue']
    venue = Venue.query.filter_by(id=venue_id).first()

    try:
        if venue:
            db.session.delete(venue)
            db.session.commit()
            flash('Venue ' + venue.name + ' was successfully removed!')
    except:
        flash('Venue ' + venue.name + ' could not be deleted...!')
        db.session.rollback()
    finally:
        db.session.close()

    # return redirect(url_for('index)) does not work here
    # so it's implemented in JS
    return jsonify("success", 200)


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.filter_by(id=venue_id).first()

    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.address.data = venue.address
    form.phone.data = venue.phone
    form.genres.data = [n for n in venue.genres.split(',')]
    form.facebook_link.data = venue.facebook_link
    form.image_link.data = venue.image_link
    form.website_link.data = venue.website_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    venue = Venue.query.filter_by(id=venue_id).first()

    if venue:
        try:
            venue.name = request.form.get('name', '')
            venue.city = request.form.get('city', '')
            venue.state = request.form.get('state', '')
            venue.address = request.form.get('address', '')
            venue.genres = ','.join(request.form.getlist('genres'))
            venue.facebook_link = request.form.get('facebook_link', '')
            venue.image_link = request.form.get('image_link', '')
            venue.website_link = request.form.get('website_link', '')
            venue.seeking_venue = True if request.form.get('seeking_venue', '') == 'y' else False
            venue.seeking_description = request.form.get('seeking_description', '')
            db.session.commit()
            flash('Venue ' + request.form.get('name', '') + ' details were successfully updated!')
        except:
            db.session.rollback()
            flash('Venue ' + request.form.get('name', '') + ' details could not be updated!')
        finally:
            db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    artists = Artist.query.all()
    return render_template('pages/artists.html', artists=artists)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '')

    results = Artist.query.filter(
        Artist.name.ilike('%' + search_term + '%'),
    ).all()

    return render_template('pages/search_artists.html',
                           results=results,
                           search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    shows = Shows.query.filter_by(artist_id=artist_id).all()

    u_shows = []
    p_shows = []

    for show in shows:
        current_venue = Venue.query.filter_by(id=show.venue_id).first()
        if show.start_time <= datetime.now():
            p_shows.append({
                "venue_id": current_venue.id,
                "venue_name": current_venue.name,
                "venue_image_link": current_venue.image_link,
                "start_time": show.start_time
            })
        if show.start_time > datetime.now():
            u_shows.append({
                "venue_id": current_venue.id,
                "venue_name": current_venue.name,
                "venue_image_link": current_venue.image_link,
                "start_time": show.start_time
            })

    artist = Artist.query.filter_by(id=artist_id).first()

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website_link,
        "facebook_link": artist.facebook_link,
        "seeking_venue": True if artist.seeking_venue == 'y' else False,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "listed_on": artist.listed_on,
        "albums": artist.album,
        "past_shows": p_shows,
        "upcoming_shows": u_shows,
        "past_shows_count": len(p_shows),
        "upcoming_shows_count": len(u_shows),
    }

    return render_template('pages/show_artist.html', artist=data)


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.filter_by(id=artist_id).first()

    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.genres.data = [n for n in artist.genres.split(',')]
    form.facebook_link.data = artist.facebook_link
    form.image_link.data = artist.image_link
    form.website_link.data = artist.website_link
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    artist = Artist.query.filter_by(id=artist_id).first()

    if artist:
        try:
            artist.name = request.form.get('name', '')
            artist.city = request.form.get('city', '')
            artist.state = request.form.get('state', '')
            artist.genres = ','.join(request.form.getlist('genres'))
            artist.facebook_link = request.form.get('facebook_link', '')
            artist.image_link = request.form.get('image_link', '')
            artist.website_link = request.form.get('website_link', '')
            artist.seeking_venue = True if request.form.get('seeking_venue', '') == 'y' else False
            artist.seeking_description = request.form.get('seeking_description', '')
            db.session.commit()
            flash('Artist ' + request.form.get('name', '') + ' details were successfully updated!')
        except:
            db.session.rollback()
            flash('Artist ' + request.form.get('name', '') + ' details could not be updated!')
        finally:
            db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form_data = request.form.to_dict()
    genres = ','.join(request.form.getlist('genres'))
    seeking_venue = True if request.form.get('seeking_talent') == 'y' else False

    try:
        artist = Artist(name=form_data['name'], city=form_data['city'], state=form_data['state'],
                        phone=form_data['phone'], genres=genres, facebook_link=form_data['facebook_link'],
                        image_link=form_data['image_link'], website_link=form_data['website_link'],
                        seeking_venue=seeking_venue, seeking_description=form_data['seeking_description'])
        db.session.add(artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully created!')
    except:
        db.session.rollback()
        flash('An error occurred. Artist ' + form_data['name'] + ' could not be created.')
    finally:
        db.session.close()

    return redirect(url_for('index'))


#  Shows
#  ----------------------------------------------------------------
@app.route('/shows')
def shows():
    shows = Shows.query.all()

    data = []
    for show in shows:
        current_artist = Artist.query.filter_by(id=show.artist_id).first()
        current_venue = Venue.query.filter_by(id=show.venue_id).first()
        data.append({
            "venue_id": current_venue.id,
            "venue_name": current_venue.name,
            "artist_id": current_artist.id,
            "artist_name": current_artist.name,
            "artist_image_link": current_artist.image_link,
            "start_time": show.start_time
        })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    form = ShowForm()
    artists = Artist.query.order_by('name').all()
    venues = Venue.query.order_by('name').all()

    form.artist_id.choices = [(artist.id, artist.name) for artist in artists]
    form.venue_id.choices = [(venue.id, venue.name) for venue in venues]

    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form_data = request.form.to_dict()
    artist = Artist.query.filter_by(id=form_data['artist_id']).first()
    start_time = datetime.strptime(form_data['start_time'], '%Y-%m-%d %H:%M:%S')

    # the timedelta refers to the 3 hours between shows
    shows = Shows.query.filter_by(artist_id=artist.id).filter(between(
        Shows.start_time, start_time - timedelta(hours=3), start_time + timedelta(hours=3)
    )).all()

    # print(form_data['artist_id'])
    # print(form_data['venue_id'])

    if len(shows) <= 0:
        try:
            show = Shows(artist_id=artist.id,
                         venue_id=form_data['venue_id'],
                         start_time=form_data['start_time'])
            print(show)
            db.session.add(show)
            db.session.commit()
            flash('A new Show has been successfully listed!')
        except:
            db.session.rollback()
            flash('An error occurred. Show could not be listed.')
        finally:
            db.session.close()

            return redirect(url_for('index'))

    else:
        flash('Artist is already booked for that date!\n'
              'Please choose a date before "{}" and\n'
              'after "{}"'.format(start_time - timedelta(hours=3),
                                  start_time + timedelta(hours=3)))

    return redirect(url_for('create_shows'))


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

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
