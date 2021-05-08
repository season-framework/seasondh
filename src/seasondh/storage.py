from .base import stdClass
from .base import Configuration

import os
import pymysql
import pickle

def join(v, f='/'):
    if len(v) == 0:
        return ''
    return f.join(v)

class MySQL:
    def __init__(self, **config):
        self.config = dict()
        if 'host' in config: self.config['host'] = config['host']
        if 'port' in config: self.config['port'] = int(config['port'])
        if 'user' in config: self.config['user'] = config['user']
        if 'password' in config: self.config['password'] = config['password']
        if 'database' in config: self.config['database'] = config['database']
        if 'charset' in config: self.config['charset'] = config['charset']
        self.tablename = config['table']

    def query(self, sql, fetch=True, data=None, lastrowid=False):
        coninfo = None
        coninfo = self.config
        con = pymysql.connect(**coninfo)
        if fetch: cur = con.cursor(pymysql.cursors.DictCursor)
        else: cur = con.cursor()
        rows = cur.execute(sql, data)
        if fetch: rows = cur.fetchall()
        if lastrowid: rows = cur.lastrowid
        con.commit()
        con.close()
        return rows

    def fields(self):
        tablename = self.tablename
        columns = self.query('DESC ' + tablename)

        result = stdClass()
        result.pk = []
        result.columns = []

        for col in columns:
            if col['Key'] == 'PRI':
                result.pk.append(col['Field'])
            result.columns.append(col['Field'])
        return result

    def get(self, **values):
        try:
            tablename = self.tablename
            fields = self.fields()

            w = []
            ps = []

            for key in values:
                if key not in fields.columns: continue
                w.append('`' + key + '`=%s')
                ps.append(str(values[key]))

            w = join(w, f=' AND ')

            sql = 'SELECT * FROM `' + tablename + '` WHERE ' + w
            res = self.query(sql, data=ps, fetch=True)

            if len(res) > 0:
                return res[0]

            return None
        except Exception as e:
            return None

    def count(self, **values):
        try:
            tablename = self.tablename
            fields = self.fields()

            w = []
            ps = []

            orderby = None
            if 'orderby' in values:
                orderby = values['orderby']
                del values['orderby']

            limit = None
            if 'limit' in values:
                limit = values['limit']
                del values['limit']

            where = None
            if 'where' in values:
                where = values['where']
                del values['where']

            for key in values:
                if key not in fields.columns: continue
                w.append('`' + key + '`=%s')
                ps.append(str(values[key]))

            if len(w) > 0:
                w = join(w, f=' AND ')
                if where is not None: sql = 'SELECT count(*) as cnt FROM `' + tablename + '` WHERE (' + where + ') AND ' + w
                else: sql = 'SELECT count(*) as cnt FROM `' + tablename + '` WHERE ' + w
            elif where is not None:
                sql = 'SELECT count(*) as cnt FROM `' + tablename + '` WHERE ' + where
            else:
                sql = 'SELECT count(*) as cnt FROM `' + tablename + '`'

            if orderby is not None:
                sql = sql + ' ORDER BY ' + orderby
            if limit is not None:
                sql = sql + ' LIMIT ' + limit

            res = self.query(sql, data=ps, fetch=True)            
            return res[0]['cnt']

        except Exception as e:
            return 0

    def rows(self, **values):
        try:
            tablename = self.tablename
            fields = self.fields()

            w = []
            ps = []

            orderby = None
            if 'orderby' in values:
                orderby = values['orderby']
                del values['orderby']

            limit = None
            if 'limit' in values:
                limit = values['limit']
                del values['limit']

            where = None
            if 'where' in values:
                where = values['where']
                del values['where']

            for key in values:
                if key not in fields.columns: continue
                w.append('`' + key + '`=%s')
                ps.append(str(values[key]))

            if len(w) > 0:
                w = join(w, f=' AND ')
                if where is not None: sql = 'SELECT * FROM `' + tablename + '` WHERE (' + where + ') AND ' + w
                else: sql = 'SELECT * FROM `' + tablename + '` WHERE ' + w
            elif where is not None:
                sql = 'SELECT * FROM `' + tablename + '` WHERE ' + where
            else:
                sql = 'SELECT * FROM `' + tablename + '`'

            if orderby is not None:
                sql = sql + ' ORDER BY ' + orderby
            if limit is not None:
                sql = sql + ' LIMIT ' + limit

            res = self.query(sql, data=ps, fetch=True)            
            return res

        except Exception as e:
            return None

    def insert(self, values, **fn):
        try:
            tablename = self.tablename
            fields = self.fields()

            f = []
            v = []
            ps = []

            for key in values:
                if key not in fields.columns: continue
                f.append('`' + key + '`')
                if key in fn:
                    v.append('{}("{}")'.format(fn[key], str(values[key])))
                else:
                    v.append('%s')
                    ps.append(str(values[key]))

            f = join(f, f=',')
            v = join(v, f=',')

            sql = 'INSERT INTO `' + tablename + '`(' + f + ') VALUES(' + v + ')'
            lastrowid = self.query(sql, data=ps, fetch=False, lastrowid=True)

            return True, lastrowid
        except Exception as e:
            return False, e

    def upsert(self, values, **fn):
        try:
            tablename = self.tablename
            fields = self.fields()

            f = []
            v = []
            s = []
            ps = []

            for key in values:
                if key not in fields.columns: continue
                f.append('`' + key + '`')
                if key in fn:
                    v.append('{}("{}")'.format(fn[key], str(values[key])))
                    s.append('`{}`={}("{}")'.format(key, fn[key], str(values[key])))
                else:
                    v.append('%s')
                    s.append('`' + key + '`=%s')
                    ps.append(str(values[key]))

            f = join(f, f=',')
            v = join(v, f=',')
            s = join(s, f=',')
            ps = ps + ps

            sql = 'INSERT INTO `' + tablename + '`(' + f + ') VALUES(' + v + ') ON DUPLICATE KEY UPDATE ' + s
            res = self.query(sql, data=ps, fetch=False)

            if res == 0:
                return True, "Nothing Changed"

            return True, "Success"
        except Exception as e:
            return False, e

    def update(self, values, **where):
        try:
            tablename = self.tablename
            fields = self.fields()

            _set = []
            _where = []
            _value = []

            for key in values:
                if key not in fields.columns: continue
                v = values[key]
                if type(v) == dict:
                    _format = v['format']
                    _val = v['value']
                    _set.append(f"`{key}`={_format}")
                    _value.append(str(_val))
                else:
                    _set.append(f"`{key}`=%s")
                    _value.append(str(v))

            for key in where:
                if key not in fields.columns: continue
                v = where[key]
                if type(v) == dict:
                    val = v['value']
                    if 'op' in v:
                        op = v['op']
                        _where.append(f"`{key}`{op}%s")
                    else:
                        _where.append(f"`{key}`=%s")
                    _value.append(str(val))
                else:
                    _where.append(f"`{key}`=%s")
                    _value.append(str(v))

            _set = join(_set, f=',')
            _where = join(_where, f=' AND ')

            sql = f"UPDATE `{tablename}` SET {_set} WHERE {_where}"
            res = self.query(sql, data=_value, fetch=False)

            if res == 0:
                return True, "Nothing Changed"

            return True, "Success"
        except Exception as e:
            return False, e


class FileSystem:
    def __init__(self, **kwargs):
        self.config = Configuration(**kwargs)
        required = 'basepath'.split(',')
        for key in required:
            if self.config[key] is None:
                raise Exception(f'required option: {key}')
        self.filepath = self.config.filepath

    def files(self, page=None, dump=20):
        files = os.listdir(self.config.basepath)
        if page is None:
            return files
        page = (page - 1) * dump
        return files[page:page+dump]

    def count(self, **args):
        files = os.listdir(self.config.basepath)
        return len(files)

    def write(self, filepath=None, data=None):
        # file mode
        if data is None: raise Exception('must set ,data=data')
        try:
            if filepath is None: filepath = data.filename
            filepath = os.path.join(self.config.basepath, filepath)
            self.makedirs(filepath)
            data.save(filepath)
            return filepath[len(self.config.basepath):]
        except Exception as e:
            if filepath is None: raise Exception('must set ,filepath=filepath')
            filepath = os.path.join(self.config.basepath, str(filepath))
            ext = os.path.splitext(filepath)[1]
            if ext != '.pkl': filepath = filepath + '.pkl'
            self.makedirs(filepath)
            f = open(filepath, 'wb')
            pickle.dump(data, f)
            f.close()
            return filepath[len(self.config.basepath):]

    def read(self, filepath=None, pkl=False, default=None, as_filepath=False):
        if filepath[:len(self.config.basepath)] == self.config.basepath:
            filepath = filepath[len(self.config.basepath):]
        filepath = os.path.join(self.config.basepath, filepath)

        if as_filepath:
            return filepath

        try:
            if os.path.isfile(filepath):
                f = open(filepath, 'rb')
                ext = os.path.splitext(filepath)[1]
                if ext == '.pkl' or pkl is True:
                    data = pickle.load(f)
                else:
                    data = f.read()
                f.close()
                return data
            else:
                return os.listdir(filepath)
        except:
            return default

    def delete(self, filepath=None):
        if filepath[:len(self.config.basepath)] == self.config.basepath:
            filepath = filepath[len(self.config.basepath):]
        filepath = os.path.join(self.config.basepath, filepath)
        if os.path.isfile(filepath):
            try:
                os.remove(filepath)
                return True
            except:
                pass
        return False

    def makedirs(self, path):
        try:
            filedir = os.path.dirname(path)
            os.makedirs(filedir)
        except Exception as e:
            pass